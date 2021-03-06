from pyfor import *
import unittest

# modeled heavily after laspytest
# https://github.com/laspy/laspy/blob/master/laspytest/test_laspy.py
import pandas as pd
import laspy
import os
import matplotlib.figure
import numpy as np
import geopandas as gpd

"""
Many of these tests currently just run the function. If anyone has any more rigorous ideas, please feel free to \
implement.
"""

data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
test_las = os.path.join(data_dir, 'test.las')
test_shp = os.path.join(data_dir, 'clip.shp')
proj4str = "+proj=utm +zone=10 +ellps=GRS80 +datum=NAD83 +units=m +no_defs"

class CloudDataTestCase(unittest.TestCase):
    def setUp(self):
        self.test_points = {
            "x": [0, 1],
            "y": [0, 1],
            "z": [0, 1],
            "intensity": [0, 1],
            "classification": [0, 1],
            "flag_byte": [0, 1],
            "scan_angle_rank": [0, 1],
            "user_data": [0, 1],
            "pt_src_id": [0, 1],
            "return_num": [0,1]
        }

        self.test_header = laspy.file.File(test_las).header

        self.test_points = pd.DataFrame.from_dict(self.test_points)
        self.column = [0,1]
        self.test_cloud_data = cloud.CloudData(self.test_points, self.test_header)


    def test_init(self):
        self.assertEqual(type(self.test_cloud_data), cloud.CloudData)

    def test_data_length(self):
        self.assertEqual(len(self.test_cloud_data.points), 2)


    def test_write(self):
        self.test_cloud_data.write(os.path.join(data_dir, "temp_test_write.las"))
        read = laspy.file.File(os.path.join(data_dir, "temp_test_write.las"))
        self.assertEqual(type(read), laspy.file.File)
        read.close()

        os.remove(os.path.join(data_dir, "temp_test_write.las"))

    # TODO tear down

class CloudTestCase(unittest.TestCase):

    def setUp(self):
        self.test_cloud = cloud.Cloud(test_las)

    def test_las_load(self):
        """Tests if a .las file succesfully loads when cloud.Cloud is called"""
        self.assertEqual(type(self.test_cloud), cloud.Cloud)

    def test_grid_creation(self):
        """Tests if the grid is successfully created."""
        # Does the call to grid return the proper type
        self.assertEqual(type(self.test_cloud.grid(1)), rasterizer.Grid)

    def test_filter_z(self):
        self.test_filter = cloud.Cloud(test_las)
        self.test_filter.filter(40, 41, "z")
        self.assertEqual(self.test_filter.las.count, 3639)
        self.assertLessEqual(self.test_filter.las.max[2], [41])
        self.assertGreaterEqual(self.test_filter.las.min[2], [40])

    def test_clip_polygon(self):
        poly = gpd.read_file(test_shp)['geometry'][0]
        self.test_cloud.clip(poly)

    def test_plot_return(self):
        # FIXME broken on travis-ci
        #plot = self.test_cloud.plot(return_plot=True)
        #self.assertEqual(type(plot), matplotlib.figure.Figure)
        pass

    def test_plot(self):
        import matplotlib.pyplot as plt
        self.test_cloud.plot()
        plt.close()

    def test_plot3d(self):
        self.test_cloud.plot3d()

    def test_ground_filter_returns_raster(self):
        ground = self.test_cloud.grid(0.5).ground_filter(3, 2, 1)
        self.assertEqual(type(ground), rasterizer.Raster)
        # A very stringent test, ok to reduce:
        self.assertNotEqual(np.any(ground), 0)

    def test_normalize(self):
        test_cloud = cloud.Cloud(test_las)
        test_cloud.normalize(0.5)
        self.assertLess(test_cloud.las.max[2], 65)

    def test_chm(self):
        self.test_cloud.chm(0.5, interp_method="nearest", pit_filter= "median")

    def test_chm_without_interpolation_method(self):
        self.assertEqual(type(self.test_cloud.chm(0.5, interp_method=None)), rasterizer.Raster)

    def test_convex_hull(self):
        self.test_cloud.convex_hull



class GridTestCase(unittest.TestCase):
    def setUp(self):
        self.test_grid = cloud.Cloud(test_las).grid(1)

    def test_m(self):
        self.assertEqual(199, self.test_grid.m)

    def test_n(self):
        self.assertEqual(199, self.test_grid.n)

    def test_cloud(self):
        self.assertEqual(type(self.test_grid.cloud), cloud.Cloud)

    def test_cell_size(self):
        self.assertEqual(self.test_grid.cell_size, 1)

    def test_empty_cells(self):
        empty = self.test_grid.empty_cells
        # Check that there are the correct number
        self.assertEqual(empty.shape, (693, 2))
        # TODO Check at least one off-diagonal coordinate is non empty ([0 9] for example)

    def test_raster(self):
        raster = self.test_grid.raster("max", "z")
        self.assertEqual(type(raster), rasterizer.Raster)

    def test_interpolate(self):
        self.test_grid.interpolate("max", "z")

    def test_metrics(self):
        def custom_metric(dim):
            return(np.min(dim))

        test_metrics_dict = {
            'z': [custom_metric, np.max],
            'intensity': [np.mean]
        }

        self.test_grid.metrics(test_metrics_dict)
        self.test_grid.metrics(test_metrics_dict, as_raster=True)

    def tearDown(self):
        del self.test_grid.las.header

class RasterTestCase(unittest.TestCase):
    def setUp(self):
        pc = cloud.Cloud(test_las)
        self.test_raster = pc.grid(1).raster("max", "z")
        self.test_raster.grid.cloud.crs = proj4str

    def test_affine(self):
        affine = self.test_raster._affine
        self.assertEqual(affine[0], 1.0)
        self.assertEqual(affine[1], 0.0)
        self.assertEqual(affine[2], 405000.01000000001)
        self.assertEqual(affine[3], 0.0)
        self.assertEqual(affine[4], -1.0)
        self.assertEqual(affine[5], 3276499.9900000002)
        self.assertEqual(affine[6], 0)

    def test_watershed_seg(self):
        tops = self.test_raster.watershed_seg()
        self.assertEqual(type(tops), gpd.GeoDataFrame)
        self.assertEqual(len(tops), 289)
        self.test_raster.watershed_seg(classify=True)
        self.test_raster.watershed_seg(plot=True)

    def test_watershed_seg_out_oriented_correctly(self):
        pass

    def test_convex_hull_mask(self):
        self.test_raster._convex_hull_mask

    def test_plot(self):
        self.test_raster.plot()
        self.test_raster.plot(return_plot=True)

    def test_write_with_crs(self):
        self.test_raster.write("./thing.tif")
        os.remove("./thing.tif")

    def test_write_without_crs(self):
        self.test_raster.crs = None
        self.test_raster.write("./thing.tif")



class GISExportTestCase(unittest.TestCase):
    def setUp(self):
        self.test_grid = cloud.Cloud(test_las).grid(1)
        self.test_raster = self.test_grid.raster("max", "z")

    def test_pcs_exists(self):
        print(os.path.realpath(__file__))
        pcs_path = os.path.join('..', 'pyfor', 'pcs.csv', os.path.dirname(os.path.realpath(__file__)))
        self.assertTrue(os.path.exists(pcs_path))

    def test_array_to_raster_writes(self):
        test_grid = cloud.Cloud(test_las).grid(1)
        test_grid.cloud.crs = proj4str
        array = test_grid.raster("max", "z").array
        gisexport.array_to_raster(array, 0.5, test_grid.las.header.min[0], test_grid.las.header.max[1],
                                  proj4str, os.path.join(data_dir, "temp_raster_array.tif"))
        self.assertTrue(os.path.exists(os.path.join(data_dir, "temp_raster_array.tif")))
        os.remove(os.path.join(data_dir, "temp_raster_array.tif"))

    def test_raster_output_transform(self):
        """
        Tests if the written raster output was rotated and transformed correctly.
        :return:
        """
        pass

    def test_array_to_polygon(self):
        array = np.random.randint(1, 5, size=(99, 99)).astype(np.int32)
        gisexport.array_to_polygons(array, self.test_raster._affine)

class VoxelGridTestCase(unittest.TestCase):
    def setUp(self):
        self.test_voxel_grid = voxelizer.VoxelGrid(cloud.Cloud(test_las), cell_size=2)

    def test_voxel_raster(self):
        self.test_voxel_grid.voxel_raster("count", "z")