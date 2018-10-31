# This source code is part of the Biotite package and is distributed
# under the 3-Clause BSD License. Please see 'LICENSE.rst' for further
# information.

from typing import (
    List,
    Union,
    Type,
    Sequence,
    MutableSequence,
    Tuple,
    Iterator,
    overload,
    Callable
)
import numpy as np
from .bonds import BondList
from .copyable import Copyable 


class _AtomArrayBase(Copyable):
    coord: np.ndarray
    chain_id: np.ndarray
    res_id: np.ndarray
    res_name: np.ndarray
    hetero: np.ndarray
    atom_name: np.ndarray
    element: np.ndarray
    atom_id: np.ndarray
    b_factor: np.ndarray
    occupancy: np.ndarray
    charge: np.ndarray
    bonds: Union[BondList, None]
    def __init__(self, length: int) -> None: ...
    def __add__(
        self,
        array: Union[AtomArrayStack, AtomArray]
    ) -> Union[AtomArrayStack, AtomArray]: ...
    def array_length(self) -> int: ...
    def add_annotation(self, category: str, dtype: Union[Type, str]) -> None: ...
    def del_annotation(self, category: str) -> None: ...
    def get_annotation(self, category: str) -> np.ndarray: ...
    def set_annotation(self, category: str, array: np.ndarray) -> None: ...
    def get_annotation_categories(self) -> List[str]: ...
    def equal_annotations(
        self,
        item: Union[AtomArrayStack, AtomArray]
    ) -> bool: ...
    def equal_annotation_categories(
        self,
        item: Union[AtomArrayStack, AtomArray]
    ) -> bool: ...
    def __dir__(self) -> List[str]: ...
    def __eq__(self, item: object) -> bool: ...
    def __len__(self) -> int: ...


class Atom:
    coord: np.ndarray
    chain_id: str
    res_id: int
    res_name: str
    hetero: bool
    atom_name: str
    element: str
    atom_id: int
    b_factor: float
    occupancy: float
    charge: int
    def __init__(
        self, coord: Union[List[int], np.ndarray], **kwargs
    ) -> None: ...
    def __str__(self) -> str: ...
    def __eq__(self, item: object) -> bool: ...


class AtomArray(_AtomArrayBase, Sequence[Atom]):
    def __init__(self, length: int) -> None: ...
    def get_atom(self, index: int) -> Atom: ...
    def insert(self, index: int, item: Atom) -> None: ...
    def __iter__(self) -> Iterator[Atom]: ...
    @overload
    def __getitem__(self, index: int) -> Atom: ...
    @overload
    def __getitem__(
        self, index: Union[MutableSequence[int], MutableSequence[bool], slice]
    ) -> AtomArray: ...
    def __setitem__(self, index: int, atom: Atom) -> None: ...
    def __delitem__(self, index: int) -> None: ...
    def __len__(self) -> int: ...
    def __eq__(self, item: object) -> bool: ...
    def __str__(self) -> str: ...


class AtomArrayStack(_AtomArrayBase, Sequence[AtomArray]):
    def __init__(self, depth: int, length: int) -> None: ...
    def get_array(self, index: int) -> AtomArray: ...
    def stack_depth(self) -> int: ...
    def __iter__(self) -> Iterator[AtomArray]: ...
    @overload
    def __getitem__(self, index: int) -> AtomArray: ...
    @overload
    def __getitem__(self, index: Tuple[int, int]) -> Atom: ...
    @overload
    def __getitem__(
        self, index: Tuple[
            int,
            Union[MutableSequence[int], MutableSequence[bool], slice]
        ]
    ) -> AtomArray: ...
    @overload
    def __getitem__(
        self, index: Tuple[
            Union[MutableSequence[int], MutableSequence[bool], slice],
            int
        ]
    ) -> AtomArrayStack: ...
    @overload
    def __getitem__(
        self, index: Tuple[
            Union[MutableSequence[int], MutableSequence[bool], slice],
            Union[MutableSequence[int], MutableSequence[bool], slice]
        ]
    ) -> AtomArrayStack: ...
    @overload
    def __getitem__(
        self, index: Union[MutableSequence[int], MutableSequence[bool], slice]
    ) -> AtomArrayStack: ...
    def __setitem__(self, index: int, atom: AtomArray) -> None: ...
    def __delitem__(self, index: int) -> None: ...
    def __len__(self) -> int: ...
    def __eq__(self, item: object) -> bool: ...
    def __str__(self) -> str: ...


def array(atoms: Sequence[Atom]) -> AtomArray: ...

def stack(arrays: Sequence[AtomArray]) -> AtomArrayStack: ...

def coord(
    item: Union[AtomArrayStack, AtomArray, Atom, np.ndarray]
) -> np.ndarray: ...