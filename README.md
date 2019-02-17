# Dns Updater
Update multiple domain to the ip of the current computer. All configuration is
saved on domain.json and should be mounted on **/etc/dnsupdater/domain.json** .

## Quick usage
Take [domain.json](https://github.com/pedrxd/dnsupdater/domain.json) configuration
from this repository. Modify to your needs, you can add multiple domains or
just one, just add or remove new entrys.

The **timer** variable is the time the program should wait for made a update.

For run it use:

> docker run -v /your/domain.json/:/etc/dnsupdater/domain.json pedrxd/dnsupdater


## Code from
A modified version of [this script](https://github.com/bensquire/Digital-Ocean-Dynamic-DNS-Updater) is used. Thanks to their team.
