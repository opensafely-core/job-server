import create from "zustand";

const useFileStore = create((set, get) => ({
  checkedFiles: [],

  isFileChecked: (file) =>
    get().checkedFiles.some((checked) => checked.id === file.id),
  addCheckedFile: (file) => {
    if (get().isFileChecked(file)) {
      return null;
    }

    return set((state) => ({
      checkedFiles: [{ ...file, meta: {} }, ...state.checkedFiles],
    }));
  },
  removeCheckedFile: (file) =>
    set((state) => ({
      checkedFiles: [...state.checkedFiles].filter(
        (checked) => checked.id !== file.id
      ),
    })),

  setFileMeta: (file, field, text) => {
    const fileIndex = get().checkedFiles.findIndex(
      (checked) => checked.id === file.id
    );
    Object.assign(get().checkedFiles[fileIndex], {
      meta: {
        ...get().checkedFiles[fileIndex].meta,
        [field]: text,
      },
    });

    set((state) => ({ checkedFiles: [...state.checkedFiles] }));
  },
  getFileMeta: (file, field) => {
    const fileIndex = get().checkedFiles.findIndex(
      (checked) => checked.id === file.id
    );
    return get().checkedFiles[fileIndex].meta[field];
  },

  // isAllFilesChecked: () => null,
  // addAllCheckedFiles: () => null,
  removeAllCheckedFiles: () => set(() => ({ checkedFiles: [] })),
}));

export default useFileStore;
