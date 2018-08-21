module linereader(
	input logic clk,
	input logic rst,
	
	// camera data inputs
	input logic [11:0] cam_pixel_in,
	input logic cam_hsync_in,
	input logic cam_vsync_in,
	input logic cam_clk_in,
	
	// line buffer access
	output logic [10:0] lb_addr,
	output logic [15:0] lb_data,
	output logic lb_write,
	input logic lb_ack,
	
	// status out
	output logic sr_in_hsync,
	output logic sr_in_vsync,
	output logic sr_which_line
);
		

	// the camera bus has a FIFO which synchronizes it to the main clock
	// and buffers in case the memory is busy or something
	logic cf_read, cf_write;
	logic cf_empty, cf_full;

	// camera bus data from the fifo
	logic [11:0] cam_pixel;
	logic cam_hsync, cam_vsync;
	
	cambus_fifo cambus_fifo(
		.wrclk(cam_clk_in), // camera directly writes to fifo
		.wrreq(cf_write),
		.wrfull(cf_full),
		.data({cam_hsync_in, cam_vsync_in, cam_pixel_in}),
		
		.rdclk(clk),
		.rdreq(cf_read),
		.rdempty(cf_empty),
		.q({cam_hsync, cam_vsync, cam_pixel})
	);
	
	// always write incoming pixels unless the fifo is full
	assign cf_write = !cf_full;
	
	// now there's a state machine to get bus data from the fifo
	// and write it to the line memory when appropriate
	typedef enum logic [1:0] {
		FIFO_EMPTY = 2'd0,
		TRANSFER = 2'd1,
		LINEMEM_BUSY = 2'd2
	} LBState;
	
	// state machine state
	LBState cstate, nstate;
	// frame state
	logic [8:0] pix_ctr; // which pixel of this line are we on
	logic visible; // if we are in the visible portion of the line
	
	initial begin
		cstate <= FIFO_EMPTY;
		sr_which_line <= 1'b0;
		pix_ctr <= 9'd0;
		visible <= 1'b0;
	end
	
	
	// state transition engine
	always @(posedge clk) begin
		if (!rst) begin
			// new state becomes the current
			cstate <= nstate;
			
			// increment the pixel counter if we wrote to the line memory
			if (lb_write) begin
				pix_ctr <= pix_ctr + 9'd1;
			end
			
			// handle start and end of line
			if (!visible && cam_hsync) begin
				visible <= 1'b1;
			end else if (pix_ctr == 9'd329) begin
				visible <= 1'b0;
				pix_ctr <= 9'd0;
				sr_which_line <= !sr_which_line;
			end
		end else begin
			cstate <= FIFO_EMPTY;
			sr_which_line <= 1'b0;
			pix_ctr <= 9'd0;
			visible <= 1'b0;
		end
	end
	
	// state calculation engine
	always @(*) begin
		// by default
		nstate <= cstate; // state doesn't change
		cf_read <= 1'b0; // we're not reading from the fifo
		lb_write <= 1'b0; // we're not writing to the line memory

		case (cstate)
			FIFO_EMPTY: begin
				// if the fifo isn't empty anymore
				if (!cf_empty) begin
					cf_read <= 1'b1; // queue read this cycle
					nstate <= TRANSFER; // and transfer the result next cycle,
											  // when the read is complete
				end
			end
			
			TRANSFER: begin
				// the fifo has a pixel ready to write to line memory
				lb_write <= visible; // do that now (if in visible part of line)
				if (lb_ack || !visible) begin
					// it got acknowledged
					// (or we pretend it did, during the invisible part of the line)
					if (!cf_empty) begin
						// there's more in the fifo, transfer it now
						cf_read <= 1'b1;
						nstate <= TRANSFER;
					end else begin
						// it's empty, wait for it to have stuff again
						nstate <= FIFO_EMPTY;
					end
				end else begin
					// it didn't, wait for ack
					nstate <= LINEMEM_BUSY;
				end
			end
			
			LINEMEM_BUSY: begin
				if (lb_ack) begin
					// it got acknowledged
					if (!cf_empty) begin
						// there's more in the fifo, transfer it now
						cf_read <= 1'b1;
						nstate <= TRANSFER;
					end else begin
						// it's empty, wait for it to have stuff again
						nstate <= FIFO_EMPTY;
					end
				end
			end
		endcase
	end
	
	// wire up status register and avalon interface
	assign lb_addr[0] = 1'b0;
	assign lb_addr[9:1] = pix_ctr;
	assign lb_addr[10] = sr_which_line;
	
	assign lb_data[15:12] = 4'b0;
	assign lb_data[11:0] = cam_pixel;
	
	assign sr_in_hsync = cam_hsync;
	assign sr_in_vsync = cam_vsync;
	
endmodule
