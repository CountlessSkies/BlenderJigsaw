from __future__ import absolute_import

# For Integration UI
import imp
import os
import typing
import time
import re

from System import *
from System.IO import Path, StreamWriter, File, Directory
from System.Collections.Specialized import StringCollection
from System.Text import Encoding

from Deadline.Scripting import RepositoryUtils, FrameUtils, ClientUtils, PathUtils

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

if typing.TYPE_CHECKING:
    from ThinkboxUI.Controls.Scripting.ButtonControl import ButtonControl
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

########################################################################
## Globals
########################################################################
scriptDialog = None  # type: DeadlineScriptDialog
settings = None
integration_dialog = None

ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = True

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    # type: (*str) -> None
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog

    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Blender Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Blender' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Workers.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() // 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )
    
    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a Worker has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single Worker. This is useful if the rendering application only uses one thread to render and your Workers have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Worker's Task Limit", 6, 2, "If you limit the tasks to a Worker's task limit, then by default, the Worker won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual Workers by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Deny List", 7, 2, "You can force the job to render on specific machines by using an allow list, or you can avoid specific machines by using a deny list." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The list of machines on the deny list or allow list.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Blender Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Blender File", 1, 0, "The scene file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Blender Files (*.blend);;All Files (*)", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output File (Optional)", 2, 0, "Override the output path in the scene. This is optional, and can be left blank.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "All Files (*)", 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 4, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 4, 1 , expand=False)
    scriptDialog.AddSelectionControlToGrid("SubmitSceneBox","CheckBoxControl",False,"Submit Blender Scene File With The Job", 4, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the Worker machine during rendering.")

    scriptDialog.AddControlToGrid( "ThreadsLabel", "LabelControl", "Threads", 5, 0, "The number of threads to use for rendering.", False )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox", "RangeControl", 0, 0, 256, 0, 1, 5, 1, expand=False )

    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 6, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 6, 1, expand=False )

    # Sintel
    scriptDialog.AddSelectionControlToGrid( "enableTilesBox", "CheckBoxControl", False, "Tile Rendering", 7, 0, "Enable Tile Rendering (2x2)" )
    
    scriptDialog.AddControlToGrid( "EffectiveResolutionXLabel", "LabelControl", "Effective Resolution X", 8, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "EffectiveResolutionXBox", "RangeControl", 1920, 0, 7680, 0, 1, 8, 1 )
    
    scriptDialog.AddControlToGrid( "EffectiveResolutionYLabel", "LabelControl", "Effective Resolution Y", 9, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "EffectiveResolutionYBox", "RangeControl", 1080, 0, 4320, 0, 1, 9, 1 )

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "BlenderMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    # Add Project Management and Draft Tabs
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )

    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)

    scriptDialog.EndGrid()
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","OutputBox","ThreadsBox","BuildBox", "SubmitSceneBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    appSubmission = False
    if len( args ) > 0:
        appSubmission = True
        
        if args[0] == "":
            scriptDialog.ShowMessageBox( "The Blender scene must be saved before it can be submitted to Deadline.", "Error" )
            return
        
        scriptDialog.SetValue( "SceneBox", args[0] )
        scriptDialog.SetValue( "NameBox", Path.GetFileNameWithoutExtension( args[0] ) )
        
        scriptDialog.SetValue( "FramesBox", args[1] )
        
        outputFile = args[2]
        # paddingSize = FrameUtils.GetPaddingSizeFromFilename( outputFile )
        # padding = ""
        # while len(padding) < paddingSize:
        #     padding += "#"
        
        # outputFile = FrameUtils.GetFilenameWithoutPadding( outputFile )
        # directory = Path.GetDirectoryName( outputFile )
        # prefix = Path.GetFileNameWithoutExtension( outputFile )
        # extension = Path.GetExtension( outputFile )
        # outputFile = Path.Combine( directory, prefix + padding + extension )
        
        # def get_padding_size_from_filename(file_name):
        #     # Count the number of '#' characters in the file name pattern
        #     padding_match = re.search(r'#+', file_name)  # Looks for one or more '#' symbols
        #     if padding_match:
        #         return len(padding_match.group(0))  # Return the length of the matched '#' group
        #     return None  # Return None if no padding symbols are found
        
        # paddingSize = get_padding_size_from_filename(Path.GetFileNameWithoutExtension(outputFile))
        # padding = ""
        # while len(padding) < paddingSize:
        #     padding += "#"
        directory = Path.GetDirectoryName(outputFile)
        prefix = Path.GetFileNameWithoutExtension(outputFile)
        
        extension = args[7]
        
        if extension == "JPEG2000" or extension == "JPEG":
            extension = "JPG"
        elif extension == "TARGA" or extension == "TARGA_RAW":
            extension = "TGA"
        elif extension == "CINEON":
            extension = "CIN"
        elif extension == "OPEN_EXR_MULTILAYER" or extension == "OPEN_EXR":
            extension = "EXR"
        elif extension == "FFMPEG":
            extension = "MP4"
            
        extension = "." + extension.lower()
        
        if prefix.find("#") > 0:
            outputFile = Path.Combine(directory, prefix + extension)
        else:
            outputFile = Path.Combine(directory, prefix + "####" + extension)
            # outputFile = args[7]
        
        scriptDialog.SetValue( "OutputBox", outputFile  )
        
        scriptDialog.SetValue( "ThreadsBox", int(args[3]) )
        
        platform = args[4]
        if platform.find( "64" ) >= 0:
            scriptDialog.SetValue( "BuildBox", "64bit" )
        elif platform.find( "32" ) >= 0 or platform.find( "86" ) >= 0:
            scriptDialog.SetValue( "BuildBox", "32bit" )
        else:
            scriptDialog.SetValue( "BuildBox", "None" )
            
        scriptDialog.SetValue("EffectiveResolutionXBox", int(args[5]))
        scriptDialog.SetValue("EffectiveResolutionYBox", int(args[6]))
            
        # Keep the submission window above all other windows when submitting from another app.
        scriptDialog.MakeTopMost()

    scriptDialog.ShowDialog( appSubmission )
    
def GetSettingsFilename():
    # type: () -> str
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "BlenderSettings.ini" )

def SubmitButtonPressed(*args):
    # type: (*ButtonControl) -> None
    global scriptDialog
    global integration_dialog
    
    outputFile = scriptDialog.GetValue( "OutputBox" )
    groupBatch = False
    
    # Check if Integration options are valid
    if integration_dialog is not None and not integration_dialog.CheckIntegrationSanity( outputFile ):
        return
        
    # Check if blender files exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "The Blender file %s does not exist" % sceneFile, "Error" )
        return
    elif (not scriptDialog.GetValue("SubmitSceneBox") and PathUtils.IsPathLocal(sceneFile)):
        result = scriptDialog.ShowMessageBox( "The Blender file %s is local. Are you sure you want to continue?" % sceneFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    # Check output file
    if outputFile != "":
        if(not Directory.Exists(Path.GetDirectoryName(outputFile))):
            scriptDialog.ShowMessageBox( "The directory of the output file %s does not exist." % Path.GetDirectoryName(outputFile), "Error" )
            return
        elif( PathUtils.IsPathLocal(outputFile) ):
            result = scriptDialog.ShowMessageBox( "The output file %s is local. Are you sure you want to continue?" % outputFile, "Warning", ("Yes","No") )
            if(result=="No"):
                return
    
    frameList = []
    
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return
    else:
        frameList = FrameUtils.Parse( frames )
        
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Sintel
    effective_resolution_x = "1920"
    effective_resolution_y = "1080"
    
    effective_resolution_x = scriptDialog.GetValue("EffectiveResolutionXBox")
    effective_resolution_y = scriptDialog.GetValue("EffectiveResolutionYBox")
        
    enableTiles = scriptDialog.GetValue( "enableTilesBox" )
    regionRendering = enableTiles
    regionJobCount = 1
    batchName = jobName
    jobIds = []
    jobCount = 0
    jobResult = ""
    
    if regionRendering:
        tilesInX = 2
        tilesInY = 2
        regionJobCount = tilesInX * tilesInY
        
    for jobNum in range(regionJobCount):
        modifiedName = jobName
        if regionRendering:
            modifiedName = modifiedName + " - Tile " + str(jobNum)
            
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "blender_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Blender" )
        writer.WriteLine( "Name=%s" % modifiedName )
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
        writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
        writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
        writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
        
        writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        
        if outputFile != "":
            directory = Path.GetDirectoryName( outputFile )
            prefix = Path.GetFileNameWithoutExtension( outputFile )
            extension = Path.GetExtension( outputFile )
            if extension == "":
                extension = ".png"
            if not regionRendering:
                if outputFile.find( "#" ) < 0:
                    outputFile = Path.Combine( directory, prefix + "####" + extension )
                writer.WriteLine( "OutputFilename0=%s" % outputFile )
            else:
                tempOutputFile = outputFile
                if outputFile.find( "#" ) < 0:
                    tileFile = Path.Combine( directory, "tile_?_" + prefix + "####" + extension )
                else:
                    tileFile = Path.Combine(directory, "tile_?_" + prefix + extension)
                tempOutputFile = tileFile.replace("?", str(jobNum))
                writer.WriteLine("OutputFilename0=%s" % tempOutputFile)
                
        if regionRendering:
            groupBatch = True

        # Integration
        extraKVPIndex = 0

        if integration_dialog is not None and integration_dialog.IntegrationProcessingRequested():
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()

        if groupBatch:
            writer.WriteLine( "BatchName=%s\n" % ( batchName ) ) 
        writer.Close()

        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "blender_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        
        if regionRendering:
            writer.WriteLine("RegionRendering=True")
            writer.WriteLine( "CurrentTile=%s" % jobNum )
            
        if(not scriptDialog.GetValue("SubmitSceneBox")):
            writer.WriteLine("SceneFile=" + sceneFile)
        
        if outputFile != "":
            writer.WriteLine( "OutputFile=%s" % outputFile )
        
        writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
        writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
        
        writer.Close()
    
        # Setup the command line arguments.
        arguments = StringCollection()
    
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        if scriptDialog.GetValue( "SubmitSceneBox" ):
            arguments.Add( sceneFile )
    
        # Now submit the job.
        jobResult = results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        jobId = ""
        resultArray = jobResult.split("\n")
        for line in resultArray:
            if line.startswith("JobID="):
                jobId = line.replace("JobID=", "")
                jobID = jobId.strip()
                break
            
        jobIds.append(jobID)
        jobCount += 1
        
    # Sintel Assembly
    if regionRendering:
        jobName = scriptDialog.GetValue("NameBox")
        jobName = "%s - Assembly" % (jobName)
        
        # Create submission info file
        jigsawJobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "jigsaw_submit_info.job" )
        jigsawPluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "jigsaw_plugin_info.job" )  
        
        writer = StreamWriter( jigsawJobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=DraftTileAssembler" )
        writer.WriteLine( "Name=%s" % jobName )
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
        writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
        writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
        writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
        writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
        
        writer.WriteLine( "JobDependencies=%s" % ",".join(jobIds) )
        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=1" )
        
        writer.WriteLine( "BatchName=%s" % ( batchName ) )
        
        writer.Close()
        
        # Creating plugin info file
        writer = StreamWriter( jigsawPluginInfoFilename, False, Encoding.Unicode )
        
        # writer.WriteLine( "ErrorOnMissing=%s" % (scriptDialog.GetValue( "ErrorOnMissingCheck" )) )
        # writer.WriteLine( "ErrorOnMissingBackground=%s" % (scriptDialog.GetValue( "ErrorOnMissingBackgroundCheck" )) )
        # writer.WriteLine( "CleanupTiles=%s" % (scriptDialog.GetValue( "CleanupTilesCheck" )) )
        writer.WriteLine( "MultipleConfigFiles=True" )
        
        writer.Close()
        
        configFiles = []
        
        def get_padding_size_from_filename(file_name):
            # Count the number of '#' characters in the file name pattern
            padding_match = re.search(r'#+', file_name)  # Looks for one or more '#' symbols
            if padding_match:
                return len(padding_match.group(0))  # Return the length of the matched '#' group
            return None  # Return None if no padding symbols are found
        
        paddingSize = get_padding_size_from_filename(Path.GetFileNameWithoutExtension(outputFile))
        padding = ""
        while len(padding) < paddingSize:
            padding += "#"
            
        for frame in frameList:
            imageFileName = outputFile.replace("\\", "/")
            
            tileName = imageFileName
            outputName = imageFileName
            
            if not imageFileName.find("#") > 0:
                outputName = imageFileName
            else:
                outputName = imageFileName.replace(padding, str(frame).zfill(paddingSize))
                
            directory = Path.GetDirectoryName(outputName)
            prefix = Path.GetFileNameWithoutExtension(outputName)
            extension = Path.GetExtension(outputName)
            
            tileName = Path.Combine(directory, "tile_?_" + prefix + extension)
            
            date = time.strftime("%Y_%m_%d_%H_%M_%S")
            configFilename = os.path.join(ClientUtils.GetDeadlineTempPath(), os.path.basename(outputName) + "_" + str(frame) + "_config_" + date + ".txt" )
            configFilename = configFilename.replace("\\", "/")
            
            writer = StreamWriter( configFilename, False, Encoding.Unicode )
            writer.WriteLine( "" )
            writer.WriteLine( "ImageFileName=" + outputName )
            
            writer.WriteLine( "TilesCropped=True" )
            writer.WriteLine( "TileCount=" + str( tilesInX * tilesInY ) )
            writer.WriteLine( "DistanceAsPixels=False" )
            
            writer.WriteLine("ImageWidth=%s" % effective_resolution_x)
            writer.WriteLine("ImageHeight=%s" % effective_resolution_y)
            
            # Sinte hardcoded config file
            writer.WriteLine("Tile0FileName=%s" % (Path.Combine(directory, "tile_0_") + prefix + extension).replace("\\","/"))
            writer.WriteLine("Tile0X=0")
            writer.WriteLine("Tile0Y=0")
            writer.WriteLine("Tile1FileName=%s" % (Path.Combine(directory, "tile_1_") + prefix + extension).replace("\\","/"))
            writer.WriteLine("Tile1X=0.5")
            writer.WriteLine("Tile1Y=0")
            writer.WriteLine("Tile2FileName=%s" % (Path.Combine(directory, "tile_2_") + prefix + extension).replace("\\","/"))
            writer.WriteLine("Tile2X=0")
            writer.WriteLine("Tile2Y=0.5")
            writer.WriteLine("Tile3FileName=%s" % (Path.Combine(directory, "tile_3_") + prefix + extension).replace("\\","/"))
            writer.WriteLine("Tile3X=0.5")
            writer.WriteLine("Tile3Y=0.5")
            
            writer.Close()
            configFiles.append(configFilename)
            
        arguments = []
        arguments.append(jigsawJobInfoFilename)
        arguments.append(jigsawPluginInfoFilename)
        arguments.extend(configFiles)
        jobResult = ClientUtils.ExecuteCommandAndGetOutput(arguments)
        jobCount += 1
        
    scriptDialog.ShowMessageBox( results, "Submission Results" )
