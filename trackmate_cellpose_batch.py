from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.io import TmXmlWriter
from fiji.plugin.trackmate.util import LogRecorder;
#from fiji.plugin.trackmate.tracking.sparselap import SparseLAPTrackerFactory
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
# from fiji.plugin.trackmate.tracking import LAPUtils
from fiji.plugin.trackmate.util import TMUtils
from fiji.plugin.trackmate.visualization.hyperstack import HyperStackDisplayer
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate.cellpose import CellposeDetectorFactory
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettings
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettings
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.action import CaptureOverlayAction
from  fiji.plugin.trackmate.action import LabelImgExporter
from fiji.plugin.trackmate.cellpose.CellposeSettings import PretrainedModel

from ij import IJ
from datetime import datetime as dt
import sys 
import os
import time

reload(sys)
sys.setdefaultencoding('utf-8')

# ------------------------------------------------------
# 	EDIT FILE PATHS BELOW.
# ------------------------------------------------------
# Shall we save the xml file?
saveXML = True
# Shall we display the results each time?
show_output = True
# can define a set up root directories for analysis
rootdirs = ['E:/trackmate-cellpose/'] 

tif_subfolder_name = 'trackmate-cellpose_test_data/'
label_subfolder_name = 'TM-CP_output/Labeled_imgs/' 
trackim_subfolder_name = 'TM-CP_output/track_imgs/'

# define number of frames
nFrame = 4 
# filter track duration: keep tracks > DURATION_THRESHOLD% of total duration
duration_threshold = 50 

# print(file_paths[0])

# ------------------------------------------------------
# 	ACTUAL CODE.
# ------------------------------------------------------
def run( rootdir, tif_path , label_path, trackim_path):
	# Get image file paths and names
	file_paths = []
	fNames = []
	for fname in os.listdir(tif_path):
		if  '.tif' in fname:
		    file_paths.append(tif_path + fname) 
		    fNames.append(fname)    
	
	# go through all files
	for f in range(len(fNames)):  
		thisImPath = file_paths[f]
		thisImName = fNames[f]
		print(str(f+1)+' / '+str(len(fNames)) +', masking for '+ thisImName)
		start = time.time() # time of this processing start
		# Open image.
		imp  = IJ.openImage( thisImPath )
		cal = imp.getCalibration()
	
		# Logger -> content will be saved in the XML file.
		logger = LogRecorder( Logger.VOID_LOGGER )
		logger.log( 'TrackMate-Cellpose analysis script\n' )
		dt_string = dt.now().strftime("%d/%m/%Y %H:%M:%S")
		logger.log( dt_string + '\n\n' )
	
		#------------------------
		# Prepare settings object
		#------------------------
	
		settings = Settings(imp)
		setup = settings.toStringImageInfo() 
	
		# Configure Cellpose default detector.
		
		settings.detectorFactory = CellposeDetectorFactory()
		
		settings.detectorSettings['TARGET_CHANNEL'] = 0
		settings.detectorSettings['OPTIONAL_CHANNEL_2'] = 0
		# define CellPose environment path below
		settings.detectorSettings['CELLPOSE_PYTHON_FILEPATH'] = 'C:/Users/ellin/anaconda3/envs/cellpose/python.exe' 
		# change Cellpose model directory and model name below
		settings.detectorSettings['CELLPOSE_MODEL_FILEPATH'] = 'C:/Users/ellin/.cellpose/models/cyto3'	
		settings.detectorSettings['CELLPOSE_MODEL'] = PretrainedModel.CUSTOM # PretrainedModel.CYTO2
		settings.detectorSettings['CELL_DIAMETER'] =30.0
		settings.detectorSettings['USE_GPU'] = True 
		settings.detectorSettings['SIMPLIFY_CONTOURS'] = True
	
	
		# Configure tracker
		settings.trackerFactory = SparseLAPTrackerFactory()
		# settings.trackerSettings = LAPUtils.getDefaultLAPSettingsMap()
		settings.trackerSettings = settings.trackerFactory.getDefaultSettings()
		# Define tracking settings below
		settings.trackerSettings[ 'LINKING_MAX_DISTANCE' ] 		= 30.0 
		settings.trackerSettings[ 'GAP_CLOSING_MAX_DISTANCE' ]	= 30.0
		settings.trackerSettings[ 'MAX_FRAME_GAP' ]				= 3
		settings.initialSpotFilterValue = -1.
	
		# Analyzers 
		settings.addAllAnalyzers()
	
		##  Add some filters for tracks/spots 
	
		# filter track duration = keep tracks > DURATION_THRESHOLD% of total duration 
		minduration = (duration_threshold/100.0) * int(nFrame) # int(nFrame/10)            
		filter1_track = FeatureFilter('TRACK_DURATION', minduration, True) 
		settings.addTrackFilter(filter1_track)
	
		# filter on spot = keep spots having radius > 1.6 um, and circularity > 0.7
		#filter1_spot = FeatureFilter('RADIUS', 1.6, True)
		#filter2_spot = FeatureFilter('CIRCULARITY', 0.7, True)
		#settings.addSpotFilter(filter1_spot)
		#settings.addSpotFilter(filter2_spot)
	
		print "Spot filters added = ", settings.getSpotFilters()
		print "Track filters added = ", settings.getTrackFilters()
	
		#-------------------
		# Instantiate plugin
		#-------------------
	
		trackmate = TrackMate( settings )
		trackmate.computeSpotFeatures( True )
		trackmate.computeTrackFeatures( True )
		trackmate.getModel().setLogger( logger )
	
		#--------
		# Process
		#--------
	
		ok = trackmate.checkInput()
		if not ok:
		    print( str( trackmate.getErrorMessage() ) )
		    return
	
		ok = trackmate.process()
		if not ok:
		    print( str( trackmate.getErrorMessage() ) )
		    return
	
		#----------------
		# Save results
		#----------------
		# dave xml file
		if saveXML:
			saveFile = TMUtils.proposeTrackMateSaveFile( settings, logger )
			#saveFile = label_path
			writer = TmXmlWriter(saveFile, logger)
			writer.appendLog( logger.toString() )
			writer.appendModel( trackmate.getModel() )
			writer.appendSettings( trackmate.getSettings() )
			writer.writeToFile();
			print( "Xml saved to: " + saveFile.toString() + '\n' );
	
		#----------------
		# Display results
		#----------------
	
		if show_output:
			model = trackmate.getModel()
			selectionModel = SelectionModel( model )
			ds = DisplaySettings()
			ds = DisplaySettingsIO.readUserDefault()
			ds.spotDisplayedAsRoi = True
			displayer =  HyperStackDisplayer( model, selectionModel, imp, ds )
			displayer.render()
			displayer.refresh()
			
			# capture overlay - RGB file and save
			image = trackmate.getSettings().imp
			capture = CaptureOverlayAction.capture(image, -1, imp.getNFrames(), logger)
			capture.setTitle("TracksOverlay")
			capture.show()
			IJ.save(capture, trackim_path + 'Tracks_' + thisImName[0:-4]+ ".tif")
			capture.close()
		
		# export labeled image
		exportSpotsAsPxls = False
		exportTracksOnly = True
		useIDAsLabel = False
		lblImg = LabelImgExporter.createLabelImagePlus(trackmate, exportSpotsAsPxls, exportTracksOnly, useIDAsLabel )
		lblImg.setTitle("Labeled image")
		lblImg.show()
		IJ.save(lblImg, label_path + 'LblImg_' + thisImName[0:-4]+ ".tif")
		lblImg.close()
		end = time.time()
		print "The time of trackmate-cellpose processing for this image : ",end-start," sec"

# -------------------------------------------------
for rootdir in rootdirs:
	dt_string = dt.now().strftime("%d/%m/%Y %H:%M:%S")
	print( '\nRunning analysis on %s - %s' % ( rootdir, dt_string ))
	tif_path = rootdir + tif_subfolder_name 
	label_path = rootdir + label_subfolder_name
	trackim_path = rootdir + trackim_subfolder_name
	
	if not os.path.exists(tif_path):
	    print('Tif path '+tif_path+' does not exist') 
	if not os.path.exists(label_path):
	        os.makedirs(label_path) 
	if not os.path.exists(trackim_path):
	        os.makedirs(trackim_path) 
	run(rootdir, tif_path , label_path, trackim_path)
print('Finished!')



