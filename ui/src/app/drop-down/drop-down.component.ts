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

import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';

import {SelectionData} from '../models/types';

/** A drop down component. */
@Component({
  selector: 'app-drop-down',
  templateUrl: './drop-down.component.html',
  styleUrls: ['./drop-down.component.scss']
})
export class DropDownComponent implements OnInit {
  @Input() controllerName?: string;
  @Input() label?: string;
  @Input() className?: string;
  @Input() isMultiple?: boolean;
  @Input() isRequired?: boolean;
  @Input({required: true}) values!: SelectionData[];

  @Output() readonly selectionEvent = new EventEmitter<SelectionData[]>();

  names: string[] = [];

  control = new FormControl();

  ngOnInit() {
    if (this.isRequired) {
      this.control.addValidators(Validators.required);
    }
  }

  onChange(selection: SelectionData[]) {
    this.selectionEvent.emit(selection);
  }
}
