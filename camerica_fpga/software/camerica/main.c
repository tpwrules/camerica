#include <string.h>
#include <inttypes.h>

// this system's definitions
#include "system.h"

#include "io.h"
#include "sys/alt_stdio.h"
#include "sys/alt_driver.h"
#include "sys/alt_irq.h"

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

int main() {
	alt_printf("Hello and welcome!\n");
	uint32_t frame_counter = 0;
	IOWR_HW_REGS_FRAME_COUNTER(0);
	
	// configure the DMA controller for doubleword transfers
	// that's the only thing it can do
	// also tell it to use length to end the transaction
	IOWR_ALTERA_AVALON_DMA_LENGTH(VID_DMA_BASE, 0);
	IOWR_ALTERA_AVALON_DMA_CONTROL(VID_DMA_BASE,
		ALTERA_AVALON_DMA_CONTROL_DWORD_MSK | // enable 64 bit transfers
		ALTERA_AVALON_DMA_CONTROL_LEEN_MSK  | // stop transfer when length == 0
		ALTERA_AVALON_DMA_CONTROL_GO_MSK); // turn on dma
	
	while (1) {
		// wait until the HPS wants DMA to be enabled
		while (!(IORD_HW_REGS_STATUS() & HW_REGS_STATUS_DMA_ENABLED));
		uint32_t dma_phys_addr = IORD_HW_REGS_DMA_PHYS_ADDR();
		alt_printf("the dma address: %x\n", dma_phys_addr);
		// capture frames forever (or until HPS wants DMA disabled)
		while ((IORD_HW_REGS_STATUS() & HW_REGS_STATUS_DMA_ENABLED)) {
			// tell the HPS that the DMA is enabled
			IOWR_HW_REGS_CONTROL(
				IORD_HW_REGS_CONTROL() | HW_REGS_CONTROL_DMA_ACTIVE);
			// dma to the start of a new frame in physical memory
			uint32_t curr_line_addr_dest = ((frame_counter & 0xF) << 18) +
				dma_phys_addr;
			// wait until the camera deasserts VBLANK and the frame is visible
			while ((IORD_HW_REGS_STATUS() & HW_REGS_STATUS_VBLANK));
			for (int line=0; line<(CAM_LINES_PER_FRAME); line++) {
				// configure the DMA controller while the frame is happening
				// dma from the line that's currently being filled
				IOWR_ALTERA_AVALON_DMA_RADDRESS(VID_DMA_BASE,
					(IORD_HW_REGS_STATUS() & HW_REGS_STATUS_WHICH_LINE) ? 0x400 : 0x000);
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
				while (!(IORD_ALTERA_AVALON_DMA_STATUS(VID_DMA_BASE) &
					ALTERA_AVALON_DMA_STATUS_DONE_MSK));
				// and clear the DONE status
				IOWR_ALTERA_AVALON_DMA_STATUS(VID_DMA_BASE, 0);
				// now wait for HBLANK to complete
				while ((IORD_HW_REGS_STATUS() & HW_REGS_STATUS_HBLANK));
			}
			// copy the histogram over too, in the future
			// write the updated frame count
			IOWR_HW_REGS_FRAME_COUNTER(++frame_counter);
			// and set the bit to tell the HPS
			IOWR_HW_REGS_CONTROL(
				IORD_HW_REGS_CONTROL() & HW_REGS_CONTROL_SET_FRAME_READY);
			// wait for VBLANK to begin, we don't do anything then
			while (!(IORD_HW_REGS_STATUS() & HW_REGS_STATUS_VBLANK));
			//alt_printf("got it!\n");
		}
		// tell HPS that DMA is actually disabled
		IOWR_HW_REGS_CONTROL(IORD_HW_REGS_CONTROL() & ~HW_REGS_CONTROL_DMA_ACTIVE);
	}
	while(1) {
		uint32_t dma_phys_addr = IORD_HW_REGS_DMA_PHYS_ADDR();
		alt_printf("current phys addr: %x\n", dma_phys_addr);
		alt_getchar();
	}
	return 0;
}

	/*
  IOWR_ALTERA_AVALON_DMA_LENGTH(DMA_0_BASE, 0);
	IOWR_ALTERA_AVALON_DMA_CONTROL(DMA_0_BASE,
			ALTERA_AVALON_DMA_CONTROL_WORD_MSK | // half-word (16 bit) transfers
			ALTERA_AVALON_DMA_CONTROL_LEEN_MSK | // end transaction by length
			ALTERA_AVALON_DMA_CONTROL_GO_MSK // and go!
	);
	*/

  // register the linereader management interrupt
  //alt_irq_register(LINEREADER_STATUS_REG_IRQ, 0, linereader_int);
	//alt_ic_isr_register(LR_STATUS_IRQ_INTERRUPT_CONTROLLER_ID,
     //   LR_STATUS_IRQ,
	//		linereader_int, 0, 0);
  // enable edge capture and ints of such
 // IOWR_ALTERA_AVALON_PIO_IRQ_MASK(LR_STATUS_BASE, CAM_HSYNC | CAM_VSYNC);

  //while (1)
//	  alt_printf("frames: %x\n", total_frames);


