# Tutorial Bonus

This bonus tutorial explains how to extend the *Getting started* workflow to compute the average distance of the spots to the nuclei contours.

SimpleITK provides the function [`sitk.SignedMaurerDistanceMap()`](https://simpleitk.org/doxygen/v2_0/html/namespaceitk_1_1simple.html#a756e4bd805e8f8fc75091162f1f2c1fb) which returns the distance of all pixels of a binary image to the closest contour. 

This can be used to generate a grayscale image where each pixel's value represents its distance to the nearest contour — positive values inside the nuclei and negative values outside.

Then, we will just need to get the value of this image at the center of the connected components (spots) to get its distance.
In fact, we will look at the minimum value of the connected component to get the distance of the clostest pixel of the connected component to the contour.

For this, we will need the `label_statistics` node which computes a set of statistics for each connected component from the SimpleITK class [`LabelStatisticsImageFilter()`](https://simpleitk.org/doxygen/v2_0/html/classitk_1_1simple_1_1LabelStatisticsImageFilter.html).

The "Sitk signed maurer distance map" node takes a binary image as input. Thus, we need to binarize our Sam segmentation. We will use a simple "Binary threshold" node.

Open the *Getting started* workflow and add a "Binary threshold" node (SimpleITK > Custom > Binary threshold). Connect it after the "Sam" node.
Make sure its `image` parameter is set to the "Sam: segmentation" column, and set `upperThreshold` to 1 (let the other parameters untouched to obtain the following: `{"image": "Sam: segmentation", "channel": 0, "lowerThreshold": 0, "upperThreshold": 1, "insideValue": 1, "outsideValue": 0}`).

Add a "Sitk signed maurer distance map" node after the "Binary threshold". Let the default options so that it computes distances from the output of the Binary threshold node.

Add two "Concat" nodes (after the "Sitk signed maurer distance map" node) to concatenate the DataFrames from the "Connected component" nodes and the "Sitk signed maurer distance map" node, and rename them accordingly. This will enable us to send both to the "Label statistics" nodes.

Connect the output of the "Connected component 1" node to the input of the "Concat 1" node and do the same for the other pair of nodes. Connect the output of "Sitk signed maurer distance map" to the input of the "Concat" nodes.

Add two "Label statistics" nodes after the "Concat" nodes and select it to adjust its parameters. 
Use the "Sitk signed maurer distance map: image" column for the `image` parameter, and the "Connected component 0/1: image" for the `label` image.
Adjust the `maxSize` parameter to 600.

Compute the workflow to see the statistics of the connected components.

Finally, we want to compute the average distance of the spots to the contour. We need to create a custom tool which will process the output DataFrames of the "Label statistics" nodes for this purpose.

Create a new custom tool by clicking the "Create tool" button in the "Tools" tab.
Enter "Average distance to contour" for the name and click OK.

Past the following code to the tool script:

```python
import pandas
import numpy as np

class Tool():

    name = "Compute average distance to contour"
    description = "Compute the average distance between spots and nucleus contours."
    categories = ['Workflow']
    environment = 'bioimageit'
    dependencies = dict(python='==3.10')
    inputs = []
    outputs = []
    
    def processDataFrame(self, dataFrame, argsList):
        if 'label_index' not in dataFrame.columns: return pandas.DataFrame()

        # Only consider the spots which are inside the nucleus (those for which the minimum distance value is greater than 0)
        dataFrame = dataFrame[dataFrame['minimum']>0]

        # Create a minimum_distance column from the square root of the minim
        dataFrame['minimum_distance'] = np.sqrt(dataFrame['minimum'].abs())

        # Groups the rows by image (to get one group per image) and compute the mean of the minimum distance column in this group
        # Rename the result "average_distance_to_contour" and return a DataFrame from this
        average_distance_to_contour = dataFrame.groupby('image')['minimum_distance'].mean().reset_index(name='average_distance_to_contour')
        return pandas.DataFrame(average_distance_to_contour).reset_index()
```

Save the file and execute the workflow in BioImageIT, you get the average distances of the spots to the nucleus contours for all images!