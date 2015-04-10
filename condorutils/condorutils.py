import re
import os

__all__ = ['getJobs', 'getSubContent', 'getSubVariables', 'getSubArguments', 'getSubCommand']

def getJobs(dagFileName, subFileName):
    with open(dagFileName) as dag:
        content = dag.read()

    # Identify the job that relates to this sub file.
    subFileName = re.escape(os.path.basename(subFileName))
    matches = re.findall(r'^JOB (\w+) .*{file}$'.format(file=subFileName), content, re.MULTILINE)
    return [m.strip() for m in matches]

def getSubContent(subFileName):
    subContent = {}
    with open(subFileName, 'r') as sub:
        matches = re.findall(r'^(.+?)\s+=\s+(.+)$', sub.read(), re.MULTILINE)
        for k, v in matches:
            subContent[k.strip()] = v.strip()
    return subContent

def getSubVariables(dagFileName, subFileName):
    # Identify the job that relates to this sub file.
    jobs = getJobs(dagFileName, subFileName)
    assert len(jobs) > 0, 'Couldn\'t find jobs.'

    with open(dagFileName, 'r') as dag:
        dagContent = dag.read()

    subVariables = []
    for j in jobs:
        # Locate and extract the argument key/value pairs.
        s = {}
        match = re.search(r'^VARS {job}.+$'.format(job=re.escape(j)), dagContent, re.MULTILINE)
        matches = re.findall(r'(\w+)="(.*?)"', match.group(0))
        for k, v in matches:
            s[k] = v
        subVariables.append(s)

    return subVariables

def getSubArguments(subContent=None, subVariables=None, dagFileName=None, subFileName=None):
    if subContent is None or subVariables is None:
        if dagFileName is None and subFileName is None:
            raise ValueError('Insufficient information.')

        subContent = getSubContent(subFileName)
        subVariables = getSubVariables(dagFileName, subFileName)

    return [re.sub(r'\$\((\w+)\)', lambda m: v[m.group(1)], subContent['arguments'].strip(' \'"')) for v in subVariables]

def getSubCommand(subContent=None, subVariables=None, dagFileName=None, subFileName=None):
    if subContent is None or subVariables is None:
        if dagFileName is None and subFileName is None:
            raise ValueError('Insufficient information.')

        subContent = getSubContent(subFileName)
        subVariables = getSubVariables(dagFileName, subFileName)

    subArguments = getSubArguments(subContent=subContent, subVariables=subVariables)
    return ['{executable} {arguments}'.format(executable=subContent['executable'], arguments=a)
            for a in subArguments]
