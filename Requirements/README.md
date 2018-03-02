Make sure that your executable mentionned in `etc/common.cfg` point to binaries included here, or some other location on your machine for software installed externally from this repository.

## Git submodules
- run `git submodule update --init --recursive` from the project root
  - This will fetch dependencies from other git repositories.
  - Currently: RSEM (forked with shared memory), STAR.
  - Run `make` in `Requirements/RSEM` and `Requirements/STAR`

## SRA-Toolkit
  - add sratoolkit.2.8.2 under sratoolkit.2.8.2/
  - For example, under CENTOS7, I've used the prebuilt binary for 2.8.2 on CentOS was downloaded from: https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/2.8.2/sratoolkit.2.8.2-centos_linux64.tar.gz
   - See more distributions here here: https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/2.8.2
   - 2.8.2 is the version I've found to be best at the time. Avoid older version (for example, 2.5.0 no longer works for downloading from SRA and is obsolete.)

## Install GNU Parallel
GNU Parallel is used extensively in this pipeline. A lot of systems include it by default, but if not you can install is as so:
```
  $ # Download latest parallel version.
  $ wget https://ftp.gnu.org/gnu/parallel/parallel-latest.tar.bz2
  $ tar -xvf parallel-lastest.tar.bz2
  $ cd parallel-xxxxxxxx
  $ # Install parallel somewhere on your system, or in Requirements/ for example
  $ ./configure prefix=<Path to Requirements directory>
  $ make
  $ make install
  $ Requirements/bin/parallel --citation # Gets rid of the warning asking to cite parallel.
  $ # Make sure parallel is in your PATH
  $ export PATH=$PATH:$Requirements/bin/parallel # Or add this to your .bashrc
```
