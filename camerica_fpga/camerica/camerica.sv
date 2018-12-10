module camerica (
	// 50MHz main clock
	input logic clk,
	input logic rst,
	
	// input video bus
    input logic [15:0] vid_pixel,
    input logic vid_pixsync,
    input logic vid_hblank,
    input logic vid_vblank,
    
    output logic [3:0] cam_type,

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
	input logic [1:0] hr_address,
	input logic hr_bus_enable,
	input logic hr_rw,
	input logic [31:0] hr_write_data,
	output logic [31:0] hr_read_data,
	
	// vid mem access
	output logic vm_acknowledge,
	input logic [9:0] vm_address,
	input logic vm_bus_enable,
	input logic vm_rw,
	output logic [63:0] vm_read_data
);

	logic show_test_pattern;
	
	logic status_which_line;
	logic status_which_histo;
	
	// the linereader module actually reads the lines into memory
	linereader linereader(
		.clk(clk),
		.rst(rst),
		
		.vid_pixel(vid_pixel),
		.vid_pixsync(vid_pixsync),
		.vid_hblank(vid_hblank),
		.vid_vblank(vid_vblank),

		.vm_acknowledge(vm_acknowledge),
		.vm_address(vm_address),
		.vm_bus_enable(vm_bus_enable),
		.vm_rw(vm_rw),
		.vm_read_data(vm_read_data),
		
		.status_which_line(status_which_line),
		.status_which_histo(status_which_histo)
	);
	
	// now all the stuff for the register sets
	
	// HPS registers
	logic [31:0] hr0_dma_addr;
	logic [31:0] hr1_frame_counter;
	// status
	logic hr2_dma_active; // bit 1
	// control
	// bit 0 unused
	logic hr3_dma_enable; // bit 1
	// bit 2 unused
	logic hr3_test_pattern; // bit 3
    // bits 4-7 unused
    logic [3:0] hr3_cam_type; // bits 11-8
	
	// NIOS registers
	logic [31:0] nr0_dma_addr;
	logic [31:0] nr1_frame_counter;
	// status
	logic nr2_dma_enable; // bit 1
	// bit 2 unused
	logic nr2_which_line; // bit 3
	logic nr2_vblank; // bit 4
	logic nr2_hblank; // bit 5
	logic nr2_which_histo; // bit 6
    // bit 7 unused
    logic [3:0] nr2_cam_type; // bits 11-8
	// control
	// bit 0 unused
	logic nr3_dma_active; // bit 1
	
	// HPS writes dma addr
	assign nr0_dma_addr = hr0_dma_addr;
	// NIOS writes frame counter
	assign hr1_frame_counter = nr1_frame_counter;
	
	// cross connect dma lines
	assign hr2_dma_active = nr3_dma_active;
	assign nr2_dma_enable = hr3_dma_enable;
    
    // and camera type
    assign cam_type = hr3_cam_type;
    assign nr2_cam_type = hr3_cam_type;
	
	// remaining control signals
	assign show_test_pattern = hr3_test_pattern;
	assign nr2_vblank = vid_vblank;
	assign nr2_hblank = vid_hblank;
	assign nr2_which_line = status_which_line;
	assign nr2_which_histo = status_which_histo;
	
    logic set_nr_irq;
    logic reset_nr_irq;
	
	// HPS register access
	always @(posedge clk) begin
		hr_acknowledge <= 1'b0;
        set_nr_irq <= 1'b0;
		
		if (hr_bus_enable && !hr_acknowledge && hr_rw) begin
			// read access
			hr_acknowledge <= 1'b1;
			case (hr_address)
				2'd0: hr_read_data <= hr0_dma_addr;
				2'd1: hr_read_data <= hr1_frame_counter;
				2'd2: hr_read_data <= {30'b0,
					hr2_dma_active,
					1'b0};
				2'd3: hr_read_data <= {20'b0,
                    hr3_cam_type,
                    4'b0,
					hr3_test_pattern,
					1'b0,
					hr3_dma_enable,
					1'b0};
			endcase
		end else if (hr_bus_enable && !hr_acknowledge && !hr_rw) begin
			// write access
			hr_acknowledge <= 1'b1;
			case (hr_address)
				2'd0: hr0_dma_addr <= hr_write_data;
				2'd1: ; // writing is not possible
				2'd2: ; // writing is still not possible
				2'd3: begin
					hr3_dma_enable <= hr_write_data[1];
                    // turn on IRQ when HPS wants to turn off DMA
                    if (!hr_write_data[1])
                        set_nr_irq <= 1'b1;
					hr3_test_pattern <= hr_write_data[3];
                    hr3_cam_type <= hr_write_data[11:8];
				end
			endcase
		end
	end
	
	// NIOS register access
	always @(posedge clk) begin
		nr_acknowledge <= 1'b0;
        reset_nr_irq <= 1'b0;
		
		if (nr_bus_enable && !nr_acknowledge && nr_rw) begin
			// read access
			nr_acknowledge <= 1'b1;
			case (nr_address)
				2'd0: nr_read_data <= nr0_dma_addr;
				2'd1: nr_read_data <= nr1_frame_counter;
				2'd2: nr_read_data <= {20'b0,
                    nr2_cam_type,
                    1'b0,
					nr2_which_histo,
					nr2_hblank,
					nr2_vblank,
					nr2_which_line,
					1'b0,
					nr2_dma_enable,
					1'b0};
				2'd3: nr_read_data <= {30'b0,
					nr3_dma_active,
					1'b0};
			endcase
		end else if (nr_bus_enable && !nr_acknowledge && !nr_rw) begin
			// write access
			nr_acknowledge <= 1'b1;
			case (nr_address)
				2'd0: ; // writing is not possible
				2'd1: nr1_frame_counter <= nr_write_data;
				2'd2: ; // writing is still not possible
				2'd3: begin
					nr3_dma_active <= nr_write_data[1];
                    // reset IRQ when nios turns off DMA
                    if (!nr_write_data[1])
                        reset_nr_irq <= 1'b1;
				end
			endcase
		end
	end
	
	always @(posedge clk) begin
		if (set_nr_irq) begin
            nr_irq <= 1'b1;
        end else if (reset_nr_irq) begin
            nr_irq <= 1'b0;
        end
	end

endmodule
