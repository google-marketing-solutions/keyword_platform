/**
 * @license
 * Copyright 2023 Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Returns a flattened array that filters repeated values.
 * @returns The flattended and filtered array.
 */
export function flattenAndFilter(arrays: string[][]): string[] {
  const flatten = arrays.flat();
  const filter = flatten.filter((value, index, array) => {
    return array.indexOf(value) === index;
  });
  return filter;
}
