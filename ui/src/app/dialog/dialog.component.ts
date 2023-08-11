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

import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';

import { Output } from '../models/interfaces';

const CHAR_LIMIT = 75;

/** The dialog component to display output. */
@Component({
  selector: 'app-dialog',
  templateUrl: './dialog.component.html',
  styleUrls: ['./dialog.component.scss']
})
export class DialogComponent implements OnInit {
  assetUrls?: string[];

  constructor(@Inject(MAT_DIALOG_DATA) readonly data: Output) {}

  ngOnInit() {
    const value = this.data['value'];
    this.assetUrls = value['asset_urls'] as string[];
  }

  /** Truncates long URLs for the dialog container. */
  truncateUrl(url: string): string {
    return url.length > CHAR_LIMIT ? url.substring(0, CHAR_LIMIT) + '...' : url;
  }
}
