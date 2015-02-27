#!/usr/bin/python
# msearch provides commands: msearch, mappings.
# (lldb) msearch AAAAAA
# Found AAAAAAAAAA at 0x1045bbf86-0x1045bbf87 in r-x /tmp/x
# (lldb) mappings
# 0x000000010c431000 0x000000010c432000 r-x __TEXT                 /tmp/x

import lldb
import subprocess

# If running a command immediately after lldb started, lldb.target
# and thus lldb.process are invalid. One workaround is to run a script
# command such as 'script None' then it works. Unfortunately it only
# works when run from the interpreter, not with lldb.debugger.HandleCommand.
# The following function fixes this at runtime.
def fix_target_and_process():
  if not lldb.target.IsValid():
    lldb.target = lldb.debugger.GetSelectedTarget()
  assert lldb.target.IsValid()
  if not lldb.process.IsValid():
    lldb.process = lldb.target.GetProcess()
  assert lldb.process.IsValid()

def mappings():
  assert lldb.process.GetProcessID()
  maps = []
  r = subprocess.check_output(['vmmap', str(lldb.process.GetProcessID())])
  for e in r.split('\n'):
    if len(e) < 82 or e[39] != '-' or e[57] != '[' or e[64] != ']':
      continue
    maps.append({
        'name': e[:23].rstrip(),
        'start': int(e[23:][:16], 16),
        'end': int(e[40:][:16], 16),
        'curperm': e[66:][:3],
        'maxperm': e[70:][:3],
        'sharemode': e[77:][:3],
        'purpose': e[82:],
    })
  return sorted(maps, key=lambda x: x['start'])

def cmd_mappings(debugger, command, result, internal_dict):
  fix_target_and_process()
  for m in mappings():
    print '0x%016x 0x%016x %-3s %-22s %s' % (m['start'], m['end'], m['curperm'], m['name'], m['purpose'])

def findall(string, sub):
  i = string.find(sub)
  while i >= 0:
    yield i
    i = string.find(sub, i+1)

def msearch(pattern):
  found = []
  for m in mappings():
    if 'r' not in m['curperm']:
      continue
    error = lldb.SBError()
    b = lldb.process.ReadMemory(m['start'], m['end']-m['start'], error)
    assert error.Success(), error
    for i in findall(b, pattern):
      e = m.copy()
      e['address'] = e['start'] + i
      found.append(e)
  # filter multiple consecutive results to display 'from to' instead of multiple 'at'
  i = 0
  while i < len(found):
    # forward search for consecutive results
    o = 0
    while i+o+1 < len(found) and found[i+o+1]['address'] == found[i]['address']+o+1:
      o += 1
    # found consecutive results
    if o:
      found[i]['upto'] = found[i+o]['address']
    yield found[i]
    # continue at next non-consecutive result
    i += o+1

def cmd_msearch(debugger, command, result, internal_dict):
  fix_target_and_process()
  if not lldb.process.is_stopped:
    print >>result, 'process must be stopped first: process interrupt'
    return
  pattern = command
  for r in msearch(pattern):
    print >>result, 'Found %s at 0x%x%s in %s %s' % (
        pattern, r['address'],
        '-0x%x' % r.get('upto', '') if r.get('upto') else '',
        r['curperm'], r.get('purpose', ''))

def __lldb_init_module(debugger, internal_dict):
  lldb.debugger.HandleCommand('command script add -f msearch.cmd_msearch msearch')
  lldb.debugger.HandleCommand('command script add -f msearch.cmd_mappings mappings')
