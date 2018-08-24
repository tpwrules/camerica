module cambus (
	// the camera bus itself
	input logic cam_clk,
	input logic [11:0] cam_pixel,
	input logic cam_hsync,
	input logic cam_vsync,
	
	// output data
	output logic [11:0] pixel,
	output logic hsync,
	output logic vsync,
	output logic visible,
	output logic locked,
	
	input logic show_test_pattern
);

endmodule