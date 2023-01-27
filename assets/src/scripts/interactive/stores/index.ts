import { create } from "zustand";
import { PageCodelistGroup } from "../types";

export const useFormStore = create(() => ({
  formData: {},
}));

const pageData: PageCodelistGroup[] = [];
export const usePageData = create(() => ({
  pageData,
}));
