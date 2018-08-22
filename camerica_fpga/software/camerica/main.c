#include <string.h>
#include <inttypes.h>

// this system's definitions
#include "system.h"

#include "sys/alt_stdio.h"
#include "sys/alt_driver.h"
#include "sys/alt_irq.h"

#include "altera_avalon_dma_regs.h"
#include "altera_avalon_pio_regs.h"

#define CAM_PIXELS_PER_LINE (320)
#define CAM_LINES_PER_FRAME (240)

#define DMA_0_BASE (LB_DMA_BASE)

// read a line from the line buffer and store it in the output
void dma_receive_line(int which, int line) {

	// select line 0 or 1 based on what was asked for

	IOWR_ALTERA_AVALON_DMA_RADDRESS(DMA_0_BASE, which ? 0x400 : 0x000);
	// destination is what the user asked for
	IOWR_ALTERA_AVALON_DMA_WADDRESS(DMA_0_BASE, 0x25e00000+(line*CAM_PIXELS_PER_LINE*2));
	// set transaction length @ 2 bytes per pixel
	IOWR_ALTERA_AVALON_DMA_LENGTH(DMA_0_BASE, CAM_PIXELS_PER_LINE*2);

	// now configure the transaction and go

	// wait for the transaction to be done
	while (!(IORD_ALTERA_AVALON_DMA_STATUS(DMA_0_BASE) &
			ALTERA_AVALON_DMA_STATUS_DONE_MSK));

	// clear DONE status
	IOWR_ALTERA_AVALON_DMA_STATUS(DMA_0_BASE, 0);

}

#define CAM_HSYNC (0x1)
#define CAM_VSYNC (0x2)
void wait_for_cam(uint32_t what_for) {
	while(IORD_ALTERA_AVALON_PIO_DATA(LR_STATUS_BASE) & what_for);
	while(!(IORD_ALTERA_AVALON_PIO_DATA(LR_STATUS_BASE) & what_for));
}

void receive_frame() {
	// wait for VSync
	wait_for_cam(CAM_VSYNC);
	wait_for_cam(CAM_HSYNC);
	int which_line;
	for (int line=0; line<CAM_LINES_PER_FRAME; line++) {
		// line data is now being received
		// wait for HSync
		//wait_for_cam(CAM_VSYNC);
		//for (int wl=0; wl<line; wl++)
		wait_for_cam(CAM_HSYNC);
		// now the other line buffer is being populated
		// read which line buffer that is
		which_line = (IORD_ALTERA_AVALON_PIO_DATA(LR_STATUS_BASE) & 4) != 0;
		// and DMA in the other one (the one that was just populated)
		dma_receive_line(!which_line, line);
	}
}

volatile uint32_t total_frames;

/*

static void linereader_int(void *ctx) {
	// is this vsync?
	if (IORD_ALTERA_AVALON_PIO_DATA(LR_STATUS_BASE) & CAM_VSYNC) {
		total_frames++; // another frame has come and gone
	}

	// clear edge detector
	IOWR_ALTERA_AVALON_PIO_EDGE_CAP(LR_STATUS_BASE, 0);
}
*/

int main()
{
  IOWR_ALTERA_AVALON_DMA_LENGTH(DMA_0_BASE, 0);
	IOWR_ALTERA_AVALON_DMA_CONTROL(DMA_0_BASE,
			ALTERA_AVALON_DMA_CONTROL_WORD_MSK | // half-word (16 bit) transfers
			ALTERA_AVALON_DMA_CONTROL_LEEN_MSK | // end transaction by length
			ALTERA_AVALON_DMA_CONTROL_GO_MSK // and go!
	);

  // register the linereader management interrupt
  //alt_irq_register(LINEREADER_STATUS_REG_IRQ, 0, linereader_int);
	//alt_ic_isr_register(LR_STATUS_IRQ_INTERRUPT_CONTROLLER_ID,
     //   LR_STATUS_IRQ,
	//		linereader_int, 0, 0);
  // enable edge capture and ints of such
 // IOWR_ALTERA_AVALON_PIO_IRQ_MASK(LR_STATUS_BASE, CAM_HSYNC | CAM_VSYNC);

  //while (1)
//	  alt_printf("frames: %x\n", total_frames);

  alt_putstr("Waiting for camera to be alive\n");
  wait_for_cam(CAM_HSYNC);
  wait_for_cam(CAM_VSYNC);


	  alt_putstr("Camera is alive! Press ENTER to capture.");
	  alt_getchar();
	  alt_putstr("Capturing frames... ");
while (1) {
	  receive_frame();

	 // alt_putstr("done!\n");
  }

  return 0;
}
