import { create } from "zustand";

export const useFormStore = create(() => ({
  formData: {},
}));

export const usePageData = create(() => ({
  basePath: "",
  csrfToken: "",
  pageData: [],
}));
