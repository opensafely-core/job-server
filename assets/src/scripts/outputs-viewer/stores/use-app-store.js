import create from "zustand";

const useAppStore = create((set, get) => ({
  isModalOpen: false,
  showModal: () => set(() => ({ isModalOpen: true })),
  hideModal: () => set(() => ({ isModalOpen: false })),
}));

export default useAppStore;
