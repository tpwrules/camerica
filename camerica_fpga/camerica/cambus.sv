module cambus (
	// this module is responsible for retiming the camera bus
	// to the 50MHz clock, as well as aligning the sync signals
	input logic clk,
	input logic rst,
	
	// the camera bus itself
	input logic cam_clk,
	input logic [11:0] cam_pixel,
	input logic cam_hsync,
	input logic cam_vsync,
	
	// output data
	output logic [11:0] vid_pixel,
	output logic vid_pixsync,
	output logic vid_hsync,
	output logic vid_vsync,
	output logic vid_visible,
	output logic vid_locked,
	
	input logic show_test_pattern
);

	cambus_lockdet lockdet(
		.clk(clk),
		.rst(rst),
		
		.vid_pixsync(vid_pixsync),
		.vid_hsync(vid_hsync),
		.vid_vsync(vid_vsync),
		
		.vid_locked(vid_locked)
	);
	
	// run the camera through some latches
	// to avoid metastability
	logic cam_clk_sync, cam_pixel_sync, cam_hsync_sync, cam_vsync_sync;
	
	logic [14:0] cambus1, cambus2, cambus3;
	always @(posedge clk) begin
		{cam_clk_sync, cam_pixel_sync, cam_hsync_sync, cam_vsync_sync} <= cambus3;
		cambus3 <= cambus2;
		cambus2 <= cambus1;
		cambus1 <= {cam_clk, cam_pixel, cam_hsync, cam_vsync};
	end
	
	// generate the pixsync signal on the rising edge of cam_clk
	logic cam_clk_sync_last;
	always @(posedge clk) begin
		cam_clk_sync_last <= cam_clk_sync;
	end
	assign vid_pixsync = (cam_clk_sync_last == 1'b0) && (cam_clk_sync == 1'b1);
	
	// count out the pixels and lines
	logic [8:0] pixels, lines;
	logic last_hsync, last_vsync;
	always @(posedge clk) begin
		if (!vid_locked || rst) begin
			pixels <= 9'd0;
			lines <= 9'd0;
		end else if (vid_pixsync) begin
			last_hsync <= vid_hsync;
			if ((last_hsync == 1'b0) && (vid_hsync == 1'b1)) begin
				pixels <= 9'd0;
			end else begin
				pixels <= pixels + 9'd1;
			end
			
			last_vsync <= vid_vsync;
			if ((last_vsync == 1'b0) && (vid_vsync == 1'b1)) begin
				lines <= 9'd0;
			end else begin
				lines <= lines + 9'd1;
			end
		end
	end
	
	logic h_visible, v_visible;
	assign h_visible = (pixels >= 9'd2 && pixels < 9'd322);
	assign v_visible = (lines >= 9'd1 && lines < 9'd259);
	assign vid_hsync = !h_visible;
	assign vid_vsync = !v_visible;
	assign vid_visible = h_visible && v_visible;

endmodule

// this module detects if the camera bus is locked
module cambus_lockdet (
	input logic clk,
	input logic rst,
	
	input logic vid_pixsync,
	input logic vid_hsync,
	input logic vid_vsync,
	
	output logic vid_locked
);

	// for now, just claim it's locked
	assign vid_locked = 1'b1;
	
endmodule