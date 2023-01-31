/* eslint-disable import/prefer-default-export */
import * as Yup from "yup";
import { usePageData } from "../stores";

export const codelistSchema = () =>
  Yup.object()
    .shape({
      label: Yup.string().required("Select a codelist"),
      organisation: Yup.string(),
      value: Yup.string().required("Select a codelist"),
      type: Yup.string()
        .oneOf(usePageData.getState().pageData.map((type) => type.id))
        .required(),
    })
    .required("Select a codelist");
