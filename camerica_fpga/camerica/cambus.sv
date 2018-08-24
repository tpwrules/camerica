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

endmodule