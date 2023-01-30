import { create } from "zustand";
import { CodelistGroup } from "../types";

export const useFormStore = create(() => ({
  formData: {},
}));

const pageData: CodelistGroup[] = [];
export const usePageData = create(() => ({
  pageData,
}));
