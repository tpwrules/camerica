module camerica (
	// 50MHz main clock
	input logic clk,
	input logic rst,
	
	// camera bus
	
	input logic cam_clk,
	input logic [11:0] cam_pixel,
	input logic cam_hsync,
	input logic cam_vsync,

	// Qsys interconnects
	
	// NIOS register access
	output logic nr_acknowledge,
	output logic nr_irq,
	input logic [1:0] nr_address,
	input logic nr_bus_enable,
	input logic nr_rw,
	input logic [31:0] nr_write_data,
	output logic [31:0] nr_read_data,
	
	// HPS register access
	output logic hr_acknowledge,
	output logic hr_irq,
	input logic [1:0] hr_address,
	input logic hr_bus_enable,
	input logic hr_rw,
	input logic [31:0] hr_write_data,
	output logic [31:0] hr_read_data,
	
	// vid mem access
	output logic vm_acknowledge,
	input logic [8:0] vm_address,
	input logic vm_bus_enable,
	input logic vm_rw,
	output logic [63:0] vm_read_data
);

	// retime the camera to the main clock
	logic [11:0] vid_pixel;
	logic vid_pixsync, vid_hblank, vid_vblank;
	logic vid_visible, vid_locked;
	cambus cambus(
		.clk(clk),
		.rst(rst),
		
		.cam_clk(cam_clk),
		.cam_pixel(cam_pixel),
		.cam_hsync(cam_hsync),
		.cam_vsync(cam_vsync),
		
		.vid_pixel(vid_pixel),
		.vid_pixsync(vid_pixsync),
		.vid_hblank(vid_hblank),
		.vid_vblank(vid_vblank),
		.vid_visible(vid_visible),
		.vid_locked(vid_locked)
	);
	
	logic status_which_line;
	logic status_which_histo;
	
	// the linereader module actually reads the lines into memory
	linereader linereader(
		.clk(clk),
		.rst(rst || !vid_locked),
		
		.vid_pixel(vid_pixel),
		.vid_pixsync(vid_pixsync),
		.vid_hblank(vid_hblank),
		.vid_vblank(vid_vblank),
		.vid_visible(vid_visible),

		.vm_acknowledge(vm_acknowledge),
		.vm_address(vm_address),
		.vm_bus_enable(vm_bus_enable),
		.vm_rw(vm_rw),
		.vm_read_data(vm_read_data),
		
		.status_which_line(status_which_line),
		.status_which_histo(status_which_histo)
	);
	

endmodule
