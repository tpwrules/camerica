#include <inttypes.h>

#include <sys/alt_irq.h>

// this system's definitions
#include "system.h"

#include "io.h"

#include "altera_avalon_dma_regs.h"

#define CAM_PIXELS_PER_LINE (320)
#define CAM_LINES_PER_FRAME (256)

#define HW_REGS_BASE (0x22000)

#define HW_REGS_DMA_PHYS_ADDR (0)

#define HW_REGS_FRAME_COUNTER (1)

#define HW_REGS_STATUS (2)
#define HW_REGS_STATUS_CAM_ACTIVE (1)
#define HW_REGS_STATUS_DMA_ENABLED (2)
#define HW_REGS_STATUS_WHICH_LINE (8)
#define HW_REGS_STATUS_VBLANK (0x10)
#define HW_REGS_STATUS_HBLANK (0x20)
#define HW_REGS_STATUS_WHICH_HISTO (0x40)

#define HW_REGS_CONTROL (3)
#define HW_REGS_CONTROL_DMA_ACTIVE (2)
#define HW_REGS_CONTROL_SET_FRAME_READY (4)

#define IORD_HW_REGS_DMA_PHYS_ADDR() (IORD(HW_REGS_BASE, HW_REGS_DMA_PHYS_ADDR))
#define IORD_HW_REGS_FRAME_COUNTER() (IORD(HW_REGS_BASE, HW_REGS_FRAME_COUNTER))
#define IORD_HW_REGS_STATUS() (IORD(HW_REGS_BASE, HW_REGS_STATUS))
#define IORD_HW_REGS_CONTROL() (IORD(HW_REGS_BASE, HW_REGS_CONTROL))

#define IOWR_HW_REGS_FRAME_COUNTER(DATA) \
	(IOWR(HW_REGS_BASE, HW_REGS_FRAME_COUNTER, DATA))
#define IOWR_HW_REGS_CONTROL(DATA) \
	(IOWR(HW_REGS_BASE, HW_REGS_CONTROL, DATA))

static void dma_off_irq(void* ctx, long unsigned int something) {
	// wait for DMA to be done
	while ((IORD_ALTERA_AVALON_DMA_STATUS(VID_DMA_BASE) &
		ALTERA_AVALON_DMA_STATUS_BUSY_MSK));
	// tell HPS that it's done
	IOWR_HW_REGS_CONTROL(IORD_HW_REGS_CONTROL() & ~HW_REGS_CONTROL_DMA_ACTIVE);
	// and reset the NIOS to start the process over
	NIOS2_WRITE_STATUS(0);
	NIOS2_WRITE_IENABLE(0);
	((void (*) (void)) NIOS2_RESET_ADDR) ();
}

int main() {
	IOWR_HW_REGS_FRAME_COUNTER(0);
	
	// configure the DMA controller for doubleword transfers
	// that's the only thing it can do
	// also tell it to use length to end the transaction
	IOWR_ALTERA_AVALON_DMA_LENGTH(VID_DMA_BASE, 0);
	IOWR_ALTERA_AVALON_DMA_CONTROL(VID_DMA_BASE,
		ALTERA_AVALON_DMA_CONTROL_DWORD_MSK | // enable 64 bit transfers
		ALTERA_AVALON_DMA_CONTROL_LEEN_MSK  | // stop transfer when length == 0
		ALTERA_AVALON_DMA_CONTROL_GO_MSK); // turn on dma
	
	// enable the DMA turnoff notification IRQ
	alt_irq_register(NIOS_VID_REGS_IRQ, 0, dma_off_irq);
	alt_irq_cpu_enable_interrupts();

	// wait until the HPS wants DMA to be enabled
	while (!(IORD_HW_REGS_STATUS() & HW_REGS_STATUS_DMA_ENABLED));
	// "latch" the DMA destination
	uint32_t dma_phys_addr = IORD_HW_REGS_DMA_PHYS_ADDR();

	// record how many frames we've captured so we know where
	// to store and retrieve them
	uint32_t frame_counter = 0;
	IOWR_HW_REGS_FRAME_COUNTER(0);

	// wait for vblank to start so we are synchronized with frame
	while (!(IORD_HW_REGS_STATUS() & HW_REGS_STATUS_VBLANK));
	// capture until HPS wants DMA disabled
	while (1) {
		// tell the HPS that the DMA is enabled
		IOWR_HW_REGS_CONTROL(
			IORD_HW_REGS_CONTROL() | HW_REGS_CONTROL_DMA_ACTIVE);
		// dma to the start of a new frame in physical memory
		uint32_t curr_line_addr_dest = ((frame_counter & 0xF) << 18) +
			dma_phys_addr;
		// wait until the camera deasserts VBLANK and the frame is visible
		while ((IORD_HW_REGS_STATUS() & HW_REGS_STATUS_VBLANK));
		for (int line=0; line<(CAM_LINES_PER_FRAME); line++) {
			// configure the DMA controller while the line is happening
			// dma from the line that's currently being filled
			IOWR_ALTERA_AVALON_DMA_RADDRESS(VID_DMA_BASE,
				(IORD_HW_REGS_STATUS() & HW_REGS_STATUS_WHICH_LINE) ? 0x800 : 0x000);
			// and to the next line in physical memory
			IOWR_ALTERA_AVALON_DMA_WADDRESS(VID_DMA_BASE,
				curr_line_addr_dest);

			// now wait for HBLANK to be asserted, so that the line is finished
			while (!(IORD_HW_REGS_STATUS() & HW_REGS_STATUS_HBLANK));
			// and write the length so the DMA controller starts working
			IOWR_ALTERA_AVALON_DMA_LENGTH(VID_DMA_BASE,
				CAM_PIXELS_PER_LINE*2);
			curr_line_addr_dest += CAM_PIXELS_PER_LINE*2;
			// wait for the DMA controller to be finished
			while ((IORD_ALTERA_AVALON_DMA_STATUS(VID_DMA_BASE) &
				ALTERA_AVALON_DMA_STATUS_BUSY_MSK));
			// now wait for HBLANK to complete
			while ((IORD_HW_REGS_STATUS() & HW_REGS_STATUS_HBLANK));
		}
		// wait for VBLANK to begin so the histogram is finished
		while (!(IORD_HW_REGS_STATUS() & HW_REGS_STATUS_VBLANK));
		// DMA from the histogram that was just completed
		IOWR_ALTERA_AVALON_DMA_RADDRESS(VID_DMA_BASE,
			(IORD_HW_REGS_STATUS() & HW_REGS_STATUS_WHICH_HISTO) ? 0x1000 : 0x1800);
		// and put it right after the frame data
		IOWR_ALTERA_AVALON_DMA_WADDRESS(VID_DMA_BASE,
			curr_line_addr_dest);
		// write the length so the DMA controller starts working
		IOWR_ALTERA_AVALON_DMA_LENGTH(VID_DMA_BASE, 2048);
		// wait for the DMA controller to be finished
		while ((IORD_ALTERA_AVALON_DMA_STATUS(VID_DMA_BASE) &
			ALTERA_AVALON_DMA_STATUS_BUSY_MSK));
		// write the updated frame count
		IOWR_HW_REGS_FRAME_COUNTER(++frame_counter);
		// and set the bit to tell the HPS a new frame is ready
		IOWR_HW_REGS_CONTROL(
			IORD_HW_REGS_CONTROL() & HW_REGS_CONTROL_SET_FRAME_READY);
	}
}

