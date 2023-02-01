/* eslint-disable import/prefer-default-export */
import * as Yup from "yup";
import { CodelistGroup } from "../types";

export const codelistSchema = (pageData: CodelistGroup[]) =>
  Yup.object()
    .shape({
      label: Yup.string().required("Select a codelist"),
      organisation: Yup.string(),
      value: Yup.string().required("Select a codelist"),
      type: Yup.string()
        .oneOf(pageData.map((type) => type.id))
        .required(),
    })
    .required("Select a codelist");
