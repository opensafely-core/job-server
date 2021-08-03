import create from "zustand";
import { devtools } from "zustand/middleware";

const useStore = create(
  devtools(() => ({
    csrfToken: "",
    filesUrl: "",
    prepareUrl: "",
    publishUrl: "",

    listVisible: false,

    selectedFile: {
      name: "",
      url: "",
    },
  }))
);

export default useStore;
