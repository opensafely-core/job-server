import React from "react";
import toast, { Toaster, ToastBar } from "react-hot-toast";

function Toast() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        duration: Infinity,

        style: {
          whiteSpace: "pre-line",
          overflowWrap: "break-word",
          wordWrap: "break-word",
          wordBreak: "break-word",
          hyphens: "auto",
        },

        error: {
          style: {
            color: "#721c24",
            backgroundColor: "#f8d7da",
          },
        },
      }}
    >
      {(t) => (
        <ToastBar id="ToastBar" toast={t}>
          {({ icon, message }) => (
            <>
              {icon}
              {message}
              {t.type !== "loading" && (
                <button
                  className="border border-current rounded p-1 hover:bg-current hover:fill-white"
                  onClick={() => toast.dismiss(t.id)}
                  type="button"
                >
                  <span className="sr-only">Dismiss</span>
                  <svg
                    className="h-4 w-4"
                    fill="currentFill"
                    viewBox="0 0 20 20"
                    width="12"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      clipRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      fillRule="evenodd"
                    />
                  </svg>
                </button>
              )}
            </>
          )}
        </ToastBar>
      )}
    </Toaster>
  );
}

export default Toast;
