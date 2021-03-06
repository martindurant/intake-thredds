import fnmatch

from intake_xarray.base import DataSourceMixin

from .cat import ThreddsCatalog

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


class THREDDSMergedSource(DataSourceMixin):
    version = '1.0'
    container = 'xarray'
    name = 'thredds_merged'
    partition_access = True

    def __init__(self, url, path, progressbar=True, metadata=None):
        """

        Parameters
        ----------
        url : str
            Location of server
        path : list of str
            Subcats to follow; include glob characters (*, ?) in here for
            matching
        progressbar : bool
            If True, will print a progress bar. Requires `tqdm <https://github.com/tqdm/tqdm>`__
            to be installed.
        metadata : dict or None
            To associate with this source
        """
        super(THREDDSMergedSource, self).__init__(metadata=metadata)
        self.urlpath = url
        self.path = path
        self._ds = None
        self.progressbar = progressbar
        if self.progressbar and tqdm is None:
            raise ValueError("Missing package 'tqdm' required for progress bars.")

    def _open_dataset(self):
        import xarray as xr

        if self._ds is None:
            cat = ThreddsCatalog(self.urlpath)
            for i in range(len(self.path)):
                part = self.path[i]
                if '*' not in part and '?' not in part:
                    cat = cat[part]()
                else:
                    break
            path = self.path[i:]
            if self.progressbar:
                data = [ds.to_dask() for ds in tqdm(_match(cat, path), desc='Dataset(s)', ncols=79)]
            else:
                data = [ds.to_dask() for ds in _match(cat, path)]
            self._ds = xr.combine_by_coords(data, combine_attrs='override')


def _match(cat, patterns):
    out = []
    for name in cat:
        if fnmatch.fnmatch(name, patterns[0]):
            if len(patterns) == 1:
                out.append(cat[name](chunks={}))
            else:
                out.extend(_match(cat[name](), patterns[1:]))
    return out
