import { Dialog, Transition } from "@headlessui/react";
import { useFormikContext } from "formik";
import { Fragment, useState } from "react";
import { useFormStore } from "../stores";

export default function FormDebug() {
  const formik = useFormikContext();
  const state = useFormStore();
  const [isOpen, setIsOpen] = useState(false);

  function closeModal() {
    setIsOpen(false);
  }

  function openModal() {
    setIsOpen(true);
  }

  return (
    <>
      <div className="fixed top-1 right-1">
        <button
          className="rounded-md bg-gray-600 px-4 py-2 text-sm font-medium text-white hover:bg-opacity-30 focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75"
          onClick={openModal}
          type="button"
        >
          Debug
        </button>
      </div>

      <Transition appear as={Fragment} show={isOpen}>
        <Dialog as="div" className="relative z-50" onClose={() => closeModal()}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div aria-hidden="true" className="fixed inset-0 bg-black/30" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-screen-lg transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900"
                  >
                    Debug info
                  </Dialog.Title>
                  <div className="mt-2">
                    <pre className="my-8 p-8 bg-red-50 overflow-x-scroll">
                      {JSON.stringify(formik, null, 2)}
                    </pre>
                    <pre className="my-8 p-8 bg-bn-sun-200 overflow-x-scroll">
                      {JSON.stringify(state, null, 2)}
                    </pre>
                  </div>

                  <div className="mt-4">
                    <button
                      className="inline-flex justify-center rounded-md border border-transparent bg-blue-100 px-4 py-2 text-sm font-medium text-blue-900 hover:bg-blue-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      onClick={() => closeModal()}
                      type="button"
                    >
                      Got it, thanks!
                    </button>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </>
  );
}
