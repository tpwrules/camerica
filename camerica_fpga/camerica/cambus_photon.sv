module cambus_photon (
    // this module connects the photon camera to the 50MHz clock
    input logic clk,
    input logic rst,
    
    // the four lines from the camera
    input logic cam_DATA_CLK, // negative edge!
    input logic cam_DATA_SYNC,
    input logic cam_DATA1_OUT,
    input logic cam_DATA2_OUT,
    
    // data to the linereader
    output logic [13:0] vid_pixel,
    output logic vid_pixsync,
    output logic vid_hblank,
    output logic vid_vblank
);

    // cam_ signals are synchronous to the camera clock
    // vid_ signals are synchronous to the main 50MHz clock
    // _syncN signals are used to synchronize the two

    logic cam_rst; // the reset signal retimed to the camera clock
    logic cam_rst_sync1, cam_rst_sync2, cam_rst_sync3;
    always @(negedge cam_nclk) begin
        cam_rst <= cam_rst_sync3;
        cam_rst_sync3 <= cam_rst_sync2;
        cam_rst_sync2 <= cam_rst_sync1;
        cam_rst_sync1 <= rst === 1'b1 ? 1'b1 : 1'b0;
    end
    
    // buffer the cambus input because we have no idea
    // what the setup and hold and etc is
    // also this makes modelsim happier when simulating from VCD
    logic cam_nclk;
    assign cam_nclk = cam_DATA_CLK;
    logic cam_sync_buf;
    logic cam_data1_buf, cam_data2_buf;
    always @(negedge cam_nclk) begin
        cam_sync_buf <= cam_DATA_SYNC;
        cam_data1_buf <= cam_DATA1_OUT;
        cam_data2_buf <= cam_DATA2_OUT;
    end
    
    // unpack serial data stream from camera
    logic [13:0] cam_pixel;
    logic cam_hsync;
    logic cam_vsync;
    logic cam_new_pixel;
    
    // the camera shifts in three 7 bit words per pixel
    // and we need 2 more bits to detect the pixel boundary
    logic [8:0] cam_sync_word;
    logic [8:0] cam_data1_word, cam_data2_word;
    
    // leftmost bit is first of this pixel
    // 2 rightmost bits are start of next pixel
    // combine data1 and data2 into the pixel
    assign cam_pixel = {cam_data2_word[8:2], cam_data1_word[8:2]};
    // third bit of sync word is vsync
    assign cam_vsync = cam_sync_word[6];
    // and fifth is hsync
    assign cam_hsync = cam_sync_word[4];
    
    always @(negedge cam_nclk) begin
        // shift in the new bits
        cam_sync_word <= {cam_sync_word[7:0], cam_sync_buf};
        cam_data1_word <= {cam_data1_word[7:0], cam_data1_buf};
        cam_data2_word <= {cam_data2_word[7:0], cam_data2_buf};
        
        // if this sync bit is 1, the last was 1,
        // and the second to last was 0
        if (cam_sync_buf == 1'b1 && cam_sync_word[0] == 1'b1
                && cam_sync_word[1] == 1'b0) begin
            // then we're 2 bits into the next pixel
            // and we should store this one next cycle
            cam_new_pixel <= 1'b1;
        end else begin
            cam_new_pixel <= 1'b0;
        end
    end
    
    // use FIFO to take pixels from the vid domain
    logic fifo_rdempty, fifo_rdreq;
    logic [15:0] fifo_out;
    cambus_photon_fifo fifo(
        .data({cam_hsync, cam_vsync, cam_pixel}),
        .wrclk(cam_nclk),
        .wrreq(cam_new_pixel),
        
        .q(fifo_out),
        .rdclk(clk),
        .rdreq(fifo_rdreq),
        .rdempty(fifo_rdempty)
    );
    
    // automatically read pixels as they become ready
    assign fifo_rdreq = !fifo_rdempty;
    always @(posedge clk) begin
        // pixel is ready the cycle after fifo_rdreq is asserted
        vid_pixsync <= fifo_rdreq;
    end
    
    // get the pixel from the camera
    logic [13:0] vid_cam_pixel;
    // and the sync signals
    logic vid_hsync, vid_vsync;
    
    assign {vid_hsync, vid_vsync, vid_cam_pixel} = fifo_out;
    
    assign vid_hblank = !vid_hsync; // this is straightforward from the camera
    // but the pixel needs to be delayed one cycle
    always @(posedge clk) begin
        if (vid_pixsync) begin
            vid_pixel <= vid_cam_pixel;
        end
    end
    
    // the camera only outputs vid_vsync for 4 cycles
    // randomly in the middle of the blank time
    // we need to widen it to ensure the rest of the logic
    // (in particular the nios) can catch the rising edge and have time to do
    // vblank processing
    // even though it's not timed correctly relative to hblank or the frame,
    // hblank will stop pixels from being written during vblank, cause it's
    // active the whole time
    logic [10:0] vblank_timer;
    always @(posedge clk) begin
        if (vid_pixsync) begin
            if (vid_vsync) begin
                // start timer for about 2000 cycles
                vblank_timer <= 11'd2047;
                // and assert vblank
                vid_vblank <= 1'b1;
            end else if (vblank_timer != 11'd0) begin
                // decrement the timer and stay in vblank
                vblank_timer <= vblank_timer - 1'd1;
            end else begin
                // we're not in vblank once the timer expires
                vid_vblank <= 1'b0;
            end
        end
    end
endmodule