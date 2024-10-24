/**
 * @license
 * Copyright 2024 Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA} from '@angular/material/dialog';

import {Output} from '../models/interfaces';

interface DialogData {
  [key: string]: Output;
}

/** The dialog component to display output. */
@Component({
  standalone: false,
  selector: 'app-dialog',
  templateUrl: './dialog.component.html',
  styleUrls: ['./dialog.component.scss']
})
export class DialogComponent implements OnInit {
  assetUrls?: {[key: string]: string[]};

  constructor(@Inject(MAT_DIALOG_DATA) readonly data: DialogData) {}

  ngOnInit() {
    const value = this.data['value'];
    if (value) {
      this.assetUrls = value['asset_urls'] as {[key: string]: string[]};
    }
  }

  /** Generates the text for the hyperlink for download urls. */
  getFileNameFromUrl(url: string): string {
    const regex = /\/([^\/]+\.(?:csv|xlsx))/;
    const match = url.match(regex);

    if (match) {
      const fileName = match[1];
      return fileName;
    }
    return '';
  }

  /** Gets the section description for the returned filetypes. */
  getFileTypeDescription(key: string): string {
    let message = 'Unknown file type:';
    if (key === 'xlsx') {
      message =
          'Excel files (export as CSV for import into Google Ads Editor):';
    } else if (key === 'csv') {
      message = 'CSV files (for direct import into Google Ads Editor):';
    }
    return message;
  }
}
