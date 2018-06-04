import sys, os, re
"""
Background:  Assumptions

You have initialized few snapshot directories for this process. E.g. this way:
  git clone https://github.com/facebook/react.git therepo --depth 10000

 Prepare one snapshot for 2016 year while in "therepo" directory.
  git checkout `git rev-list -1 --before="Jun 1 2016" master`
  cp -r . ../react_2016
  git show -s --format=%cd --date=short > ../react_2016/.snapshot.date
  rm -rf ../react_2016/.git
  .. and similarly for 2017, 2018, ..

The file .snapshot.date is not mandatory, as you may also specify date in below input_snapshots 
list. Only one of these methods is required, and .snapshot.date is used if both defined.

"""

# Inputs: project name, team_id and input_snapshots..

# Project name
project_name = 'ReactSnapshots'

# Required only if you have multiple teams configured, otherwise leave empty.
team_id = ''  # id like adaf8a9a-fbf9-4aa4-935c-20d9c5e3771f

# Please define the directory paths, dir and date.
input_snapshots = [{
    'dir': 'react_2014',
    'date': '2014-06-01'
}, {
    'dir': 'react_2015',
    'date': '2015-06-01'
}, {
    'dir': 'react_2016',
    'date': '2016-06-01'
}, {
    'dir': 'react_2017',
    'date': '2017-06-01'
}, {
    'dir': 'react_2018',
    'date': '2018-06-01'
}]

# TODO: Other metadata about snapshots like versions, labels and tags might be also useful and could
#  be then added to the final XML model using this script.

pattern = re.compile('Project created to (.*)')

project_input_dir = ''

team_slot = ''
if team_id is not None:
    team_slot = ' --team-id ' + team_id

with os.popen('softagram createproject --project-name ' + project_name + ' ' +
              team_slot + ' 2>&1') as p:
    # in case of you have multiple teams, this command needs also --team-id argument
    output = p.read()
    m = pattern.search(output)
    if m is not None:
        project_input_dir = m.group(1)
    else:
        sys.stderr.write(output + '\n\n')
        raise Exception('Cannot create project, error..')

project_output_dir = project_input_dir.replace('/input/', '/output/')


def rename_output_dir_according_to_snapshot(snapshot, target_dir,
                                            project_output_dir):
    outputs_dir = project_output_dir + '/master'
    all_subdirs = [
        outputs_dir + '/' + d for d in os.listdir(outputs_dir)
        if os.path.isdir(outputs_dir + '/' + d)
    ]
    if len(all_subdirs) == 0:
        raise Exception('Analysis failure, no outputs created..')
    recent_output = max(all_subdirs, key=os.path.getmtime)
    snapshot_date = None
    if os.path.exists(target_dir + '/.snapshot.date'):
        # the files has like 2016-06-01
        # Correct output dir format is   2016-06-01_23-41-13Z
        snapshot_date = open(target_dir + '/.snapshot.date',
                             'r').read().splitlines()[0].strip()
    elif 'date' in snapshot:
        snapshot_date = snapshot['date']

    if snapshot_date is not None:
        output_dirname = snapshot_date + '_00-00-00Z'
        new_output_dir = outputs_dir + '/' + output_dirname
        if os.path.exists(new_output_dir):
            shutil.rmtree(
                new_output_dir
            )  # TODO Warn about overwriting previosly generated data?
        os.system('mv ' + recent_output + ' ' + new_output_dir)
        # Output is correctly renamed, TODO Now apply other snapshot metadata.
    else:
        sys.stderr.write(
            'Cannot resolve snapshot date, output directory is left without '
            'renaming..\n')


for snapshot in input_snapshots:
    target_dir = project_input_dir + '/' + project_name + '/' + project_name
    if os.path.exists(target_dir):
        raise Exception(
            'Project dir is not cleaned up properly, aborting due to {}'.
            format(target_dir))

    os.system('cp -r ' + snapshot['dir'] + ' ' + target_dir)
    os.system('softagram analyze ' + project_name + ' --force ' + team_slot)
    rename_output_dir_according_to_snapshot(snapshot, target_dir,
                                            project_output_dir)
    os.system('rm -rf ' + target_dir)

print('Ready\n')
print('Updating models index..')
os.system('docker exec -ti analyzer python3 analysis/delivery/model_index_generator.py '
          '/softagram/output /tmp')
print('Index updated.')
print('Outputs are available in ' + project_output_dir)
