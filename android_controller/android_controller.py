
## read plugin api:
## https://kupferlauncher.github.io/Documentation/PluginAPI.html

__kupfer_name__ = _('Android Controller')
__version__ = '0.1.0'
__author__ = 'Hugo Sena Ribeiro <hugosenari@gmail.com>'
__description__ = '''Control your android device with ADB'''

__kupfer_sources__ = ("DeviceSource",)
__kupfer_actions__ = ("SendToMobile",)


from kupfer.plugin_support import PluginSettings
__kupfer_settings__ = PluginSettings(
    {
        "key" : "device_dir",
        "label": "Device Dir",
        "type": str,
        "value": "/storage/sdcard0/Download"
    }
)


from kupfer.objects import Leaf, TextLeaf, FileLeaf, UrlLeaf
class DeviceLeaf(Leaf):
    def __init__(self, obj):
        Leaf.__init__(self, obj, "Android " + obj[0])

    def get_actions(self):
        for key in KEY_NAMES.keys():
            yield KeyAction(key)


from kupfer.objects import Source
class DeviceSource(Source):
    def __init__(self):
        Source.__init__(self, _("Connected Devices"))

    def get_items(self):
        out = subprocess.check_output(['adb', 'devices', '-l'])
        for line in out.split('\n')[1:]:
            if line:
                yield DeviceLeaf(
                    [ v for v in line.split(' ') if v]
                )


KEY_MUTE = 91
KEY_VOLUME_UP = 24
KEY_VOLUME_DOWN = 25
KEY_MEDIA_PLAY_PAUSE = 85
KEY_MEDIA_NEXT = 87
KEY_MEDIA_PREVIOUS = 88
KEY_MEDIA_STOP = 86

KEY_NAMES = {
    KEY_MUTE: "Mute",
    KEY_VOLUME_UP: "Volume Up",
    KEY_VOLUME_DOWN: "Volume Down",
    KEY_MEDIA_PLAY_PAUSE: "Play/Pause",
    KEY_MEDIA_NEXT: "Next Media",
    KEY_MEDIA_PREVIOUS: "Prev Media",
    KEY_MEDIA_STOP: "Stop Media"
}

import subprocess
from kupfer.objects import Action
class KeyAction(Action):
    def __init__(self, key):
        Action.__init__(self, name=KEY_NAMES[key])
        self.key = key

    def activate(self, leaf):
        device = leaf.object[0]
        subprocess.Popen([
            'adb',
            '-s',
            device,
            'shell',
            'input',
            'keyevent',
            str(self.key)
        ])

    def item_types(self):
        yield DeviceLeaf


from kupfer.obj.contacts import ContactLeaf
class SendToMobile(Action):
    def __init__(self):
        Action.__init__(self, "Send to Device")
    
    def activate(self, leaf, device_leaf):
        device = device_leaf.object[0]
        prefix = ['adb', '-s', device, 'shell', 'am', 'start']
        suffix = ['-a', 'android.intent.action.VIEW', '-d']
        
        if hasattr(leaf, 'to_android_cmd'):
            prefix, suffix = leaf.to_android_cmd(device_leaf)
        elif hasattr(leaf, 'to_android_itent'):
            suffix = leaf.to_android_itent(device_leaf)
        elif hasattr(leaf, 'view_itent'):
            suffix += leaf.view_itent(device_leaf)
        elif hasattr(leaf, 'insert_itent'):
            suffix = ['-a', 'android.intent.action.INSERT']
            suffix += leaf.insert_itent(device_leaf)
        elif isinstance(leaf, ContactLeaf):
            suffix = ['-a', 'android.intent.action.INSERT']
            suffix += ['-t', 'vnd.android.cursor.dir/person']
            for k, v in leaf.object.items():
                suffix += ['-e', k.lower(), str(v)]
        elif isinstance(leaf, FileLeaf):
            device_dir = __kupfer_settings__['device_dir']
            prefix = ['adb', '-s', device, 'push']
            suffix = [leaf.canonical_path(), device_dir]
        else:
            suffix += [str(leaf,object)]

        subprocess.Popen(prefix + suffix)
    
    def item_types(self,):
        yield UrlLeaf
        yield TextLeaf
        yield FileLeaf
        yield ContactLeaf

    def requires_object(self):
        return True

    def object_types(self):
        yield DeviceLeaf