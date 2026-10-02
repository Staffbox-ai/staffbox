ObjC.import('AppKit');
var u = $.NSURL.fileURLWithPath('__WALLPAPER__');
var ss = $.NSScreen.screens; var out = [];
for (var i = 0; i < ss.count; i++) {
  var s = ss.objectAtIndex(i);
  var ok = $.NSWorkspace.sharedWorkspace.setDesktopImageURLForScreenOptionsError(u, s, $({}), null);
  out.push(ok + ':' + ObjC.unwrap($.NSWorkspace.sharedWorkspace.desktopImageURLForScreen(s).lastPathComponent));
}
'screens ' + ss.count + ' ' + out.join(',');
