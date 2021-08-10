import create from "zustand";
import { devtools } from "zustand/middleware";

const useStore = create(
  devtools(() => ({
    authToken: "",
    basePath: "",
    csrfToken: "",
    filesUrl: "",
    prepareUrl: "",
    publishUrl: "",

    listVisible: false,

    file: {
      name: "",
      url: "",
    },
  }))
);

export default useStore;
