This is a jython code that tells imageJ to batch process images in defined folders using the TrackMate-CellPose plugin. Inputs are .tif files (time series). Outputs are .tif files after masking and tracking. 

Here, I include some sample images in "trackmate-cellpose_test_data\" for people to play with. Note that these images only have one color channel. However, including an additional neucleus channel would greatly impove masking accuracy based on my experience.

Before you start, please make sure you have the following installed:
