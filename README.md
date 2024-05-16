# Image processing service


In this Project I developed an image processing service. 
Clients send images to a Telegram chatbot, and choose a filter to apply from a links menu:


![](.img/demo.gif)


The service provides the following options:

	/blur - Apply blur filter
	/contour - Apply contour filter
	/rotate - Rotate the image
	/salt_n_pepper - Apply salt and pepper noise
	/concat - Requires 2 Images to be uploaded, & collages them together
	/segment - Segment the image


The options are to be selected from a Menu that responds to any image received by the service.
once selected the image is processed and sent back to the user with the selected filter applied.


*If the filter selected is 'concat' - an additional submenu is sent requesting the user selects a directional merge for the collage.
once selected the images are merged together and sent back, or if the images dimentions doesn't match a message will be sent back to the use to try again with matching sizes.


