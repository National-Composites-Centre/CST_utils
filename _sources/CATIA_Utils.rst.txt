CATIA_Utils
===========

This is collection of functions that allow for display of geometry stored in CompoST, displayed as geometries within CATIA part environment.

Figure below shows an example import, with displayed relimiations plines and one mesh representing a wrinkle area.

.. image:: ExampleCATIAdisplay.*
    :width: 1000
	


.. py:function:: CATIA_utils.display_file(JS=CompoST file)

	Requires CATIA to be opened already, with empty part loaded.
	Calls functions corresponding to splines, points, meshes for now.