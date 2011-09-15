import time
import android
import os
import datetime
from glob import glob
import pickle

WAIT_TIME=90
PICTURE_PATH="/sdcard/pyTimeLapse/"
PICTURE_NAME="tl%Y%m%d_%H%M%S.jpg"
LOCATION_FILE_NAME="locations_%s.pkl"


class TimeLapse(object):
    def __init__(self, geotag=True, only_capture_when_plugged_in=True):
        self.geotag = True
        self.only_capture_when_plugged_in = True
        self.locating = False
        self.droid = android.Android()
        self.picture_directory = self.getDirectory()

    def getDirectory(self):
        """
        This will return a directory including today's (in utc time) date
        This will hopefully prevent weirdness from happening if you cross a timezone 
        during the end of the day
        """
        dir_name = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        dir_full_path = os.path.join(PICTURE_PATH,dir_name)
        return dir_full_path
    

    
    def getLocation(self):
        """
        Returns a tuple of (lat, long)
        Return (None, None) if no location can be found
        """
        if not self.locating:
            self.droid.startLocating()
            self.locating = True
        location_attempt = 1
        location = {}
        result = {}
        # Try a few times to get a location
        while location_attempt<=5 and not result:
            result = self.droid.readLocation().result
            if result:
                if u"gps" in result:
                    provider = "gps"
                elif u"network" in result:
                    provider = "network"
                else:
                    # Some other provider?
                    provider = result.keys()[0]
                    print "Using unknown provider %s" % provider
                location = result[provider]
            else:
                time.sleep(0.5)
                location_attempt += 1
        return location
    
    def stopLocating(self):
        if self.locating is True:
            self.droid.stopLocating()
            self.locating = False
    
    
    def saveGeoData(self, location, picture_file):
        """
        Save the entire dictionary of geo data into a pickle file
        The key is the image name
        """
        key = os.path.basename(picture_file)
        pickle_file = os.path.join(self.picture_directory, LOCATION_FILE_NAME % os.path.basename(self.picture_directory))
        if os.path.exists(pickle_file):
            f = open(pickle_file, 'rb')
            locations = pickle.load(f)
            f.close()
        else:
            locations = {}
        locations[key] = location
        # Save to a temporary file first, then rename it
        temp_pickle = pickle_file + ".tmp"
        f = open(temp_pickle, 'wb')
        pickle.dump(locations, f)
        f.close()
        os.rename(temp_pickle, pickle_file)
    
    def is_plugged_in(self):
        """Determine if the phone is plugged in"""
        self.droid.batteryStartMonitoring()
        plug_type = self.droid.batteryGetPlugType().result
        if plug_type>=1:
            return True
        else:
            return False
        self.droid.batteryStopMonitoring()
    
    def main(self):
        # Create the directory to store the files
        if not os.path.isdir(self.picture_directory):
            os.mkdir(self.picture_directory)
    
        try:
            while True:
                if not self.only_capture_when_plugged_in or (self.only_capture_when_plugged_in and self.is_plugged_in()):
                    now = datetime.datetime.utcnow()
                    picture_file = os.path.join(self.picture_directory, now.strftime(PICTURE_NAME))
                    # Take a picture auto-focus is set to True
                    self.droid.cameraCapturePicture(picture_file, True)
                    if self.geotag is True:
                        location = self.getLocation()
                        self.saveGeoData(location, picture_file)
                else:
                    if self.geotag is True:
                        # Stop locating to preserve the battery when unplugged
                        self.stopLocating()
                time.sleep(WAIT_TIME)     
        finally:
            self.stopLocating()


if __name__ == '__main__':
    tl = TimeLapse()
    tl.main()
