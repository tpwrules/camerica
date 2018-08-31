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
	output logic vid_hblank,
	output logic vid_vblank,
	output logic vid_visible,
	output logic vid_locked,
	
	input logic show_test_pattern
);

	cambus_lockdet lockdet(
		.clk(clk),
		.rst(rst),
		
		.vid_pixsync(vid_pixsync),
		.vid_hblank(vid_hblank),
		.vid_vblank(vid_vblank),
		
		.vid_locked(vid_locked)
	);
	
	// run the camera through some latches
	// to avoid metastability
	logic cam_clk_sync, cam_hsync_sync, cam_vsync_sync;
	logic [11:0] cam_pixel_sync;
	
	logic [14:0] cambus1, cambus2, cambus3;
	always @(posedge clk) begin
		{cam_clk_sync, cam_hsync_sync, cam_vsync_sync, cam_pixel_sync} <= cambus3;
		cambus3 <= cambus2;
		cambus2 <= cambus1;
		cambus1 <= {cam_clk, cam_hsync, cam_vsync, cam_pixel};
	end
	
	// generate the pixsync signal on the rising edge of cam_clk
	// and account for one clock delay in the pixel counter
	// (realign the pixel while we're at it)
	logic cam_clk_sync_last;
	logic [11:0] vid_pixel_internal;
	logic vid_pixsync_internal;
	assign vid_pixsync_internal = 
		(cam_clk_sync_last == 1'b0) && (cam_clk_sync == 1'b1);
	always @(posedge clk) begin
		cam_clk_sync_last <= cam_clk_sync;
		vid_pixsync <= vid_pixsync_internal;
		vid_pixel_internal <= cam_pixel_sync;
	end
	
	// count out the pixels and lines
	logic [8:0] pixels, lines;
	logic last_hsync, last_vsync;
	always @(posedge clk) begin
		if (!vid_locked || rst) begin
			pixels <= 9'd0;
			lines <= 9'd0;
		end else if (vid_pixsync_internal) begin
			last_hsync <= cam_hsync_sync;
			if ((last_hsync == 1'b0) && (cam_hsync_sync == 1'b1)) begin
				pixels <= 9'd0;
				lines <= lines + 9'd1;
			end else begin
				pixels <= pixels + 9'd1;
			end
			
			last_vsync <= cam_vsync_sync;
			if ((last_vsync == 1'b0) && (cam_vsync_sync == 1'b1)) begin
				lines <= 9'd0;
			end
		end
	end
	
	logic h_visible, v_visible;
	assign h_visible = (pixels >= 9'd1 && pixels < 9'd321);
	assign v_visible = (lines >= 9'd1 && lines < 9'd259);
	assign vid_hblank = !h_visible;
	assign vid_vblank = !v_visible;
	assign vid_visible = h_visible && v_visible;
	assign vid_pixel = vid_visible ? vid_pixel_internal : 12'b0;

endmodule

// this module detects if the camera bus is locked
module cambus_lockdet (
	input logic clk,
	input logic rst,
	
	input logic vid_pixsync,
	input logic vid_hblank,
	input logic vid_vblank,
	
	output logic vid_locked
);

	// for now, just claim it's locked
	assign vid_locked = 1'b1;
	
endmodule