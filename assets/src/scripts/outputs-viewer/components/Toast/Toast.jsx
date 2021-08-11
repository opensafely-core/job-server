import React from "react";
import toast, { Toaster, ToastBar } from "react-hot-toast";

function Toast() {
  function getStyles(type) {
    if (type === "error") {
      return "danger";
    }

    if (type === "success") {
      return "success";
    }

    return "secondary";
  }

  return (
    <Toaster
      position="top-right"
      toastOptions={{
        duration: Infinity,

        error: {
          style: {
            color: "#721c24",
            backgroundColor: "#f8d7da",
          },
        },
      }}
    >
      {(t) => (
        <ToastBar toast={t}>
          {({ icon, message }) => (
            <>
              {icon}
              {message}
              {t.type !== "loading" && (
                <button
                  className={`btn btn-sm ml-2 btn-outline-${getStyles(t.type)}`}
                  onClick={() => toast.dismiss(t.id)}
                  type="button"
                >
                  <span className="sr-only">Dismiss</span>
                  <svg
                    fill="currentColor"
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
