import { mountStoreDevtool } from "simple-zustand-devtools";
import create from "zustand";

const useAppStore = create((set) => ({
  isModalOpen: false,
  showModal: () => set(() => ({ isModalOpen: true })),
  hideModal: () => set(() => ({ isModalOpen: false })),
}));

export default useAppStore;

if (process.env.NODE_ENV === "development") {
  mountStoreDevtool("Store1", useAppStore);
}
