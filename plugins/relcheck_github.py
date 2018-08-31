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
    # TODO: If API limits are reached, the (authenticated) github3 object from the
    # calling script will need to make an appearance here somehow.
    repo = github3.repository(user, repo)
    # Determine the 'best' release version.
    # This will depend on how the repository is organized and how releases are done.
    # Easiest is if the repo uses Github releases consistently. Just query that.
    # Second best is a simple semver tag. Sort and pick the latest.
    # The problem is, these release practices have to be adhered to strictly, otherwise
    # incorrect information will be harvested here.
    #
    # What heuristic can be used to get only tags that look 'release-like'?
    latestrel = repo.latest_release()
    
    verinfo['version'] = '1.2.3'
    return(verinfo)
    

def get_changelog(ref_ver_data, new_ver_data):
    changelog = 'No changelog'
    return(changelog)
