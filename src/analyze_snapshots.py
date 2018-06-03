import sys, os, re

# You may want to remove old projects first
#  docker exec -ti analyzer python3 ui/cli/softagramservice.py delete_project --project-id 9354b252-8e7b-415a-92ea-ad3a367902b6
# you may want to cleanup old outputs also..  (Warning: this removes all outputs) sudo rm -rf
# /opt/softagram/output/projects

# Inputs: project name, team_id and input_snapshots..

# Project name
project_name = 'React' 

# Required only if you have multiple teams configured, otherwise leave empty.
team_id = ''

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
    recent_output = os.listdir(outputs_dir)[-1]
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
            shutil.rmtree(new_output_dir)  # TODO Warn about overwriting previosly generated data?
        os.system('mv ' + outputs_dir + '/' + recent_output + ' ' + new_output_dir)
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

print('Ready')
print('Outputs are available in ' + project_output_dir)

