Make sure that your executable mentionned in `etc/common.cfg` point to binaries included here, or some other location on your machine for software installed externally from this repository.

## virtual environment and pip
Create a virtual environment either in the top-level of the directory or in the `scheduler` directory.
```
# Create virtual enviroment
$ virtualenv venv
# Load virtual environment
$ source venv/bin/activate
```

ALWAYS run `source venv/bin/activate` before using the pipeline to make sure you have all the python requirements loaded.

### Installing pip requirements
```
$(venv) python -m pip install --upgrade pip setuptools wheel # Upgrade packages, just in case.
$(venv) pip install -r pip-requirements.txt # Install requirements.
```
This will install the content of `pip-requirements.txt` in the `venv`.


## Git submodules
- run `git submodule update --init --recursive` from the project root
  - This will fetch dependencies from other git repositories.
  - Currently: RSEM (forked with shared memory), STAR.
  - Run `make` in `$REQUIREMENTS/RSEM`    
    - `cd $REQUIREMENTS/RSEM/ ; make`
    - `STAR` should already have pre-built binaries under `STAR/bin/Linux_x86_64_static/`.

## SRA-Toolkit
  - Add a directory for sratoolkit.X.Y.Z under `$REQUIREMENTS/sratoolkit.X.Y.Z/`
    - For example, under CENTOS7, I've used the prebuilt binary for 2.8.2 on CentOS was downloaded from: https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/2.8.2/sratoolkit.2.8.2-centos_linux64.tar.gz . I extracted it in the requirements directory and now have a directory under `$REQUIREMENTS/sratoolkit.2.8.2/`. 
   - See more distributions here: https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/
   - 2.8.2 is the version I've found to be best at the time. Avoid older version (for example, 2.5.0 no longer works for downloading from SRA and is obsolete.)

## Install GNU Parallel
GNU Parallel is used extensively in this pipeline. Your system may already have it in its environment, if so you should be able to do:
```
$ which parallel 
/usr/bin/parallel 
```
Where `/usr/bin/parallel` is where the binary is installed, and `/usr/bin/` is part of the `$PATH` environment variable. 

If parallel is not installed, you can install is as so:
```
  $ # Download latest parallel version.
  $ wget https://ftp.gnu.org/gnu/parallel/parallel-latest.tar.bz2
  $ tar -xvf parallel-lastest.tar.bz2
  $ cd parallel-xxxxxxxx
  $ # Install parallel somewhere on your system, or in Requirements/ for example
  $ ./configure prefix=<Path to Requirements directory>
  $ make
  $ make install
  $ <Path to Requirements directory>/bin/parallel --citation # Gets rid of the warning asking to cite parallel.
  $ # Make sure the full path to the parallel directory is in your PATH
  $ export PATH=$PATH:<Path to Requirements directory>/bin/parallel # Or add this to your .bashrc
```

And then you should be able to do `which  parallel` if it's set correctly. It's best to add the `export` statement in the `.bashr`/`.bash_profile` of the user(s) running the pipeline to avoid having to reconfigure the path for each bash session.
