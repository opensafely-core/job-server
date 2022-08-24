/* eslint-disable no-return-assign */
import create from "zustand";

const useFileStore = create((set, get) => ({
  checkedFiles: [],

  isFileChecked: (file) =>
    get().checkedFiles.some((checked) => checked.url === file.url),
  addCheckedFile: (file) => {
    if (get().isFileChecked(file)) {
      return null;
    }

    return set((state) => ({
      checkedFiles: [
        {
          name: file.name,
          url: file.url,
          date: file.date,
          sha256: file.sha256,
          size: file.size,
          metadata: {},
        },
        ...state.checkedFiles,
      ],
    }));
  },
  removeCheckedFile: (file) =>
    set((state) => ({
      checkedFiles: [...state.checkedFiles].filter(
        (checked) => checked.url !== file.url
      ),
    })),

  setFileMeta: (file, field, text) => {
    const fileIndex = get().checkedFiles.findIndex(
      (checked) => checked.url === file.url
    );
    Object.assign(get().checkedFiles[fileIndex], {
      metadata: {
        ...get().checkedFiles[fileIndex].metadata,
        [field]: text,
      },
    });

    set((state) => ({ checkedFiles: [...state.checkedFiles] }));
  },
  getFileMeta: (file, field) => {
    const fileIndex = get().checkedFiles.findIndex(
      (checked) => checked.url === file.url
    );
    return get().checkedFiles[fileIndex].metadata[field];
  },

  // isAllFilesChecked: () => null,
  // addAllCheckedFiles: () => null,
  removeAllCheckedFiles: () => set(() => ({ checkedFiles: [] })),

  formData: {
    files: [],
    metadata: {
      dataRelease: "",
      readAndAdhere: false,
      disclosureControls: false,
      fileTypes: false,
    },
  },
  setFormDataFiles: (files) => set(() => ({ formData: { files } })),
  setFormDataMeta: (field, val) =>
    set((state) => ({
      formData: {
        ...state.formData,
        metadata: { ...state.formData.metadata, [field]: val },
      },
    })),
  getFormDataMeta: (field) => get().formData?.metadata?.[field],
}));

export default useFileStore;
