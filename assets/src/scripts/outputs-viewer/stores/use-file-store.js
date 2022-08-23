import create from "zustand";

const useFileStore = create((set, get) => ({
  checkedFiles: [],

  isFileChecked: (id) => get().checkedFiles.some((file) => file.id === id),
  addCheckedFile: (id) => {
    if (get().isFileChecked(id)) {
      return null;
    }

    return set((state) => ({
      checkedFiles: [{ id, meta: {} }, ...state.checkedFiles],
    }));
  },
  removeCheckedFile: (id) =>
    set((state) => ({
      checkedFiles: [...state.checkedFiles].filter((file) => file.id !== id),
    })),

  setFileMeta: (id, field, text) => {
    const fileIndex = get().checkedFiles.findIndex((file) => file.id === id);
    Object.assign(get().checkedFiles[fileIndex], {
      meta: {
        ...get().checkedFiles[fileIndex].meta,
        [field]: text,
      },
    });

    set((state) => ({ checkedFiles: [...state.checkedFiles] }));
  },
  getFileMeta: (id, field) => {
    const fileIndex = get().checkedFiles.findIndex((file) => file.id === id);
    return get().checkedFiles[fileIndex].meta[field];
  },

  // isAllFilesChecked: () => null,
  // addAllCheckedFiles: () => null,
  removeAllCheckedFiles: () => set(() => ({ checkedFiles: [] })),
}));

export default useFileStore;
