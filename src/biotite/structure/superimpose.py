# This source code is part of the Biotite package and is distributed
# under the 3-Clause BSD License. Please see 'LICENSE.rst' for further
# information.

"""
This module provides functions for structure superimposition.
"""

__name__ = "biotite.structure"
__author__ = "Patrick Kunzmann, Claude J. Rogers"
__all__ = ["superimpose", "superimpose_apply", "AffineTransformation"]


import numpy as np
from .atoms import coord
from .geometry import centroid


class AffineTransformation:
    """
    An affine transformation, consisting of translations and a rotation.

    Parameters
    ----------
    center_translation : ndarray, shape=(3,) or shape=(m,3), dtype=float
        The translation vector for moving the centroid into the
        origin.
    rotation : ndarray, shape=(3,3) or shape=(m,3,3), dtype=float
        The rotation matrix.
    target_translation : ndarray, shape=(m,3), dtype=float
        The translation vector for moving the structure onto the
        fixed one.

    Attributes
    ----------
    center_translation, rotation, target_translation : ndarray
        Same as the parameters.
        The dimensions are always expanded to *(m,3)* or *(m,3,3)*,
        respectively.
    """
    def __init__(self, center_translation, rotation, target_translation):
        self.center_translation = _expand_dims(center_translation, 2)
        self.rotation = _expand_dims(rotation, 3)
        self.target_translation = _expand_dims(target_translation, 2)


    def apply(self, atoms):
        """
        Apply this transformation on the given structure.

        Parameters
        ----------
        atoms : AtomArray or AtomArrayStack or ndarray, shape(n,), dtype=float or ndarray, shape(m,n), dtype=float
            The structure to apply the transformation on.

        Returns
        -------
        transformed : AtomArray or AtomArrayStack or ndarray, shape(n,), dtype=float or ndarray, shape(m,n), dtype=float
            A copy of the `atoms` structure,
            with transformations applied.
            Only coordinates are returned, if coordinates were given in
            `atoms`.

        Examples
        --------

        >>> coord = np.arange(15).reshape(5,3)
        >>> print(coord)
        [[ 0  1  2]
         [ 3  4  5]
         [ 6  7  8]
         [ 9 10 11]
         [12 13 14]]
        >>> # Rotates 90 degrees around the z-axis
        >>> transform = AffineTransformation(
        ...     center_translation=np.array([0,0,0]),
        ...     rotation=np.array([
        ...         [0, -1,  0],
        ...         [1,  0,  0],
        ...         [0,  0,  1]
        ...     ]),
        ...     target_translation=np.array([0,0,0])
        ... )
        >>> print(transform.apply(coord))
        [[ -1.   0.   2.]
         [ -4.   3.   5.]
         [ -7.   6.   8.]
         [-10.   9.  11.]
         [-13.  12.  14.]]

        """
        mobile_coord = coord(atoms)
        original_shape = mobile_coord.shape
        mobile_coord = _reshape_to_3d(mobile_coord)
        if mobile_coord.shape[0] != self.rotation.shape[0]:
            raise IndexError(
                f"Number of transformations is {self.rotation.shape[0]}, "
                f"but number of structure models is {mobile_coord.shape[0]}"
            )

        superimposed_coord = mobile_coord.copy()
        superimposed_coord += self.center_translation[:, np.newaxis, :]
        superimposed_coord = _multi_matmul(self.rotation, superimposed_coord)
        superimposed_coord += self.target_translation[:, np.newaxis, :]

        superimposed_coord = superimposed_coord.reshape(original_shape)
        if isinstance(atoms, np.ndarray):
            return superimposed_coord
        else:
            superimposed = atoms.copy()
            superimposed.coord = superimposed_coord
            return superimposed


    def as_matrix(self):
        """
        Get the translations and rotation as a combined 4x4
        transformation matrix.

        Multiplying this matrix with coordinates in the form
        *(x, y, z, 1)* will apply the same transformation as
        :meth:`apply()` to coordinates in the form *(x, y, z)*.

        Returns
        -------
        transformation_matrix : ndarray, shape=(m,4,4), dtype=float
            The transformation matrix.
            *m* is the number of models in the transformation.

        Examples
        --------

        >>> coord = np.arange(15).reshape(5,3)
        >>> print(coord)
        [[ 0  1  2]
         [ 3  4  5]
         [ 6  7  8]
         [ 9 10 11]
         [12 13 14]]
        >>> # Rotates 90 degrees around the z-axis
        >>> transform = AffineTransformation(
        ...     center_translation=np.array([0,0,0]),
        ...     rotation=np.array([
        ...         [0, -1,  0],
        ...         [1,  0,  0],
        ...         [0,  0,  1]
        ...     ]),
        ...     target_translation=np.array([0,0,0])
        ... )
        >>> print(transform.apply(coord))
        [[ -1.   0.   2.]
         [ -4.   3.   5.]
         [ -7.   6.   8.]
         [-10.   9.  11.]
         [-13.  12.  14.]]
        >>> # Use a 4x4 matrix for transformation as alternative
        >>> coord_4 = np.concatenate([coord, np.ones((len(coord), 1))], axis=-1)
        >>> print(coord_4)
        [[ 0.  1.  2.  1.]
         [ 3.  4.  5.  1.]
         [ 6.  7.  8.  1.]
         [ 9. 10. 11.  1.]
         [12. 13. 14.  1.]]
        >>> print((transform.as_matrix()[0] @ coord_4.T).T)
        [[ -1.   0.   2.   1.]
         [ -4.   3.   5.   1.]
         [ -7.   6.   8.   1.]
         [-10.   9.  11.   1.]
         [-13.  12.  14.   1.]]

        """
        n_models = self.rotation.shape[0]
        rotation_mat = _3d_identity(n_models, 4)
        rotation_mat[:, :3, :3] = self.rotation
        center_translation_mat = _3d_identity(n_models, 4)
        center_translation_mat[:, :3, 3] = self.center_translation
        target_translation_mat = _3d_identity(n_models, 4)
        target_translation_mat[:, :3, 3] = self.target_translation
        return target_translation_mat @ rotation_mat @ center_translation_mat


def _expand_dims(array, n_dims):
    """
    Expand the dimensions of an `ndarray` to a certain number of
    dimensions.
    """
    while array.ndim < n_dims:
        array = array[np.newaxis, ...]
    return array


def _3d_identity(m, n):
    """
    Create an array of *m* identity matrices of shape *(n, n)*
    """
    matrices = np.zeros((m, n, n), dtype=float)
    indices = np.arange(n)
    matrices[:, indices, indices] = 1
    return matrices


def superimpose(fixed, mobile, atom_mask=None):
    """
    Superimpose structures onto a fixed structure.

    The superimposition is performed using the Kabsch algorithm
    :footcite:`Kabsch1976, Kabsch1978`, so that the RMSD between the
    superimposed and the fixed structure is minimized.

    Parameters
    ----------
    fixed : AtomArray, shape(n,) or AtomArrayStack, shape(m,n) or ndarray, shape(n,), dtype=float or ndarray, shape(m,n), dtype=float
        The fixed structure.
        Alternatively coordinates can be given.
    mobile: AtomArray, shape(n,) or AtomArrayStack, shape(m,n) or ndarray, shape(n,), dtype=float or ndarray, shape(m,n), dtype=float
        The structure(s) which is/are superimposed on the `fixed`
        structure.
        Each atom at index *i* in `mobile` must correspond the
        atom at index *i* in `fixed` to obtain correct results.
        Alternatively coordinates can be given.
    atom_mask: ndarray, dtype=bool, optional
        If given, only the atoms covered by this boolean mask will be
        considered for superimposition.
        This means that the algorithm will minimize the RMSD based
        on the covered atoms instead of all atoms.
        The returned superimposed structure will contain all atoms
        of the input structure, regardless of this parameter.

    Returns
    -------
    fitted : AtomArray or AtomArrayStack or ndarray, shape(n,), dtype=float or ndarray, shape(m,n), dtype=float
        A copy of the `mobile` structure(s),
        superimposed on the fixed structure.
        Only coordinates are returned, if coordinates were given in
        `mobile`.
    transformation : AffineTransformation
        This object contains the affine transformation(s) that were
        applied on `mobile`.
        :meth:`AffineTransformation.apply()` can be used to transform
        another AtomArray in the same way.

    Notes
    -----
    The `transformation` can come in handy, in case you want to
    superimpose two
    structures with different amount of atoms.
    Often the two structures need to be filtered in order to obtain the
    same size and annotation arrays.
    After superimposition the transformation can be applied on the
    original structure using :meth:`AffineTransformation.apply()`.

    References
    ----------

    .. footbibliography::

    Examples
    --------

    At first two models of a structure are taken and one of them is
    randomly rotated/translated.
    Consequently the RMSD is quite large:

    >>> array1 = atom_array_stack[0]
    >>> array2 = atom_array_stack[1]
    >>> array2 = translate(array2, [1,2,3])
    >>> array2 = rotate(array2, [1,2,3])
    >>> print("{:.3f}".format(rmsd(array1, array2)))
    11.260

    RMSD decreases after superimposition of only CA atoms:

    >>> array2_fit, transformation = superimpose(
    ...     array1, array2, atom_mask=(array2.atom_name == "CA")
    ... )
    >>> print("{:.3f}".format(rmsd(array1, array2_fit)))
    1.961

    RMSD is even lower when all atoms are considered in the
    superimposition:

    >>> array2_fit, transformation = superimpose(array1, array2)
    >>> print("{:.3f}".format(rmsd(array1, array2_fit)))
    1.928
    """
    # Bring coordinates into the same dimensionality
    mob_coord = _reshape_to_3d(coord(mobile))
    fix_coord = _reshape_to_3d(coord(fixed))

    if atom_mask is not None:
        # Implicitly this creates array copies
        mob_filtered = mob_coord[:, atom_mask, :]
        fix_filtered = fix_coord[:, atom_mask, :]
    else:
        mob_filtered = np.copy(mob_coord)
        fix_filtered = np.copy(fix_coord)

    # Center coordinates at (0,0,0)
    mob_centroid = centroid(mob_filtered)
    fix_centroid = centroid(fix_filtered)
    mob_centered_filtered = mob_filtered - mob_centroid[:, np.newaxis, :]
    fix_centered_filtered = fix_filtered - fix_centroid[:, np.newaxis, :]

    rotation = _get_rotation_matrices(
        fix_centered_filtered, mob_centered_filtered
    )
    transform = AffineTransformation(-mob_centroid, rotation, fix_centroid)
    return transform.apply(mobile), transform


def superimpose_apply(atoms, transformation):
    """
    Superimpose structures using a given :class:`AffineTransformation`.

    The :class:`AffineTransformation` can be obtained by prior
    superimposition.

    DEPRECATED: Use :func:`AffineTransformation.apply()` instead.

    Parameters
    ----------
    atoms : AtomArray or ndarray, shape(n,), dtype=float
        The structure to apply the transformation on.
        Alternatively coordinates can be given.
    transformation: AffineTransformation
        The transformation, obtained by :func:`superimpose()`.

    Returns
    -------
    fitted : AtomArray or AtomArrayStack
        A copy of the `atoms` structure,
        with transformations applied.
        Only coordinates are returned, if coordinates were given in
        `atoms`.

    See Also
    --------
    superimpose
    """
    return transformation.apply(atoms)


def _reshape_to_3d(coord):
    """
    Reshape the coordinate array to 3D, if it is 2D.
    """
    if coord.ndim < 2:
        raise ValueError(
            "Coordinates must be at least two-dimensional"
        )
    if coord.ndim == 2:
        return coord[np.newaxis, ...]
    elif coord.ndim == 3:
        return coord
    else:
        raise ValueError(
            "Coordinates must be at most three-dimensional"
        )


def _get_rotation_matrices(fixed, mobile):
    """
    Get the rotation matrices to superimpose the given mobile
    coordinates into the given fixed coordinates, minimizing the RMSD.

    Uses the *Kabsch* algorithm.
    Both sets of coordinates must already be centered at origin.
    """
    # Calculate cross-covariance matrices
    cov = np.sum(fixed[:,:,:,np.newaxis] * mobile[:,:,np.newaxis,:], axis=1)
    v, s, w = np.linalg.svd(cov)
    # Remove possibility of reflected atom coordinates
    reflected_mask = (np.linalg.det(v) * np.linalg.det(w) < 0)
    v[reflected_mask, :, -1] *= -1
    matrices = np.matmul(v, w)
    return matrices


def _multi_matmul(matrices, vectors):
    """
    Calculate the matrix multiplication of m matrices
    with m x n vectors.
    """
    return np.transpose(
        np.matmul(
            matrices,
            np.transpose(vectors, axes=(0, 2, 1))
        ),
        axes=(0, 2, 1)
    )
