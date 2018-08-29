# Github-specific version update checker
# Two functions
#   get_version()
#   get_changelog()

import github3

def get_version(dep_id=None):
    print('dep_id = {}'.format(dep_id)) 
    verinfo = {}
    user = dep_id.split('/')[0]
    repo = dep_id.split('/')[1]
    repo = github3.repository(user, repo)
    
    verinfo['version'] = '1.2.3'
    return(verinfo)
    

def get_changelog(ref_ver_data, new_ver_data):
    changelog = 'No changelog'
    return(changelog)
