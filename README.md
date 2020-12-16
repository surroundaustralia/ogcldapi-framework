![](ogc-ld-api.png)

# OGC API LD Framework
This is a Linked Data API framework that is also conformant with the [_OGC API: Features_ specification](http://www.opengis.net/doc/IS/ogcapi-features-1/1.0).

Expected use is for this code to draw from a data source that fully characterises the API instance' content, i.e. no special configuration of this API should be made, other than specification of the data source (an RDFlib Graph *store* or other). Specialised HTML styling, if desired, will need to be applied to this API too, within the `view/` module (folder) which contains CSS styling and HTML templates.

Extensions to the data model implemented can be made through extending the classes within the `model/` module.

Multiple instances of this framework are in operations, online:

* <http://provinces.surroundaustralia.com/> - Australian Geological Provinces Database
* <https://w3id.org/dggs/asgs-api> - ASGS as OGC API
* <https://w3id.org/dggs/geofabric-api> - Geofabric DGGS as OGC API
* <https://w3id.org/dggs/tb16pix-api> - TB16Pix as OGC API



## Installation
1. Ensure Python 3 in available on your system
2. Clone this repo
3. Install requirements in *requirements.txt*, e.g. `~$ pip3 install -r requirements.txt`


## License  
This code is licensed using the GPL v3 licence. See the [LICENSE file](LICENSE) for the deed. 

Note [Citation](#citation) below for attribution.


## Citation
To cite this software, please use the following BibTex:

```
@software{w3id.org-dggs-ogcldapi,
  author = {{Nicholas J. Car}},
  title = {OGCLDPI: A Linked Data and OGC API framework written in Python},
  version = {0.5},
  date = {2020},
  publisher = "SURROUND Australia Pty. Ltd.",
  url = {https://dggs.org/object?uri=https://w3id.org/dggs/ogcldapi}
}
```


## Contacts

*publisher:*  
![](style/SURROUND-logo-100.png)  
**SURROUND Australia Pty. Ltd.**  
<https://surroundaustralia.com>  

*creator:*  
**Dr Nicholas J. Car**  
*Data Systems Architect*  
SURROUND Australia Pty. Ltd.  
<nicholas.car@surroudaustralia.com>  