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

import {AfterViewInit, ChangeDetectorRef, Component, EventEmitter, OnInit, Output, QueryList, ViewChildren} from '@angular/core';
import {AbstractControl, FormControl, FormGroup, ValidationErrors, ValidatorFn} from '@angular/forms';
import {MatCheckbox} from '@angular/material/checkbox';
import {MatSlideToggle} from '@angular/material/slide-toggle';

import {Selection, Translation} from '../models/interfaces';
import {SelectionGroup} from '../models/types';
import {TranslationService} from '../services/translation.service';
import {SingleSelectComponent} from '../single-select/single-select.component';

type componentGroup = MatSlideToggle|MatCheckbox;

enum TranslationControl {
  SOURCE_LANGUAGE = 'source-language',
  TARGET_LANGUAGE = 'target-language',
  GLOSSARY = 'glossary'
}

/**
 * A translation component.
 *
 * TODO(): Consider creating abstract/base class for this component
 * as there are other components that follow the same pattern/logic.
 */
@Component({
  selector: 'app-translation',
  templateUrl: './translation.component.html',
  styleUrls: ['./translation.component.scss']
})
export class TranslationComponent implements OnInit, AfterViewInit {
  @Output()
  readonly translationValidationErrorEvent = new EventEmitter<boolean>();

  form = new FormGroup({});

  glossaries!: Selection[];
  languages!: Selection[];

  glossaryId?: string;
  sourceLanguageCode?: string;
  targetLanguageCode?: string;

  showSpinner = false;
  shortenTranslationsToCharLimit = false;
  translateAds = true;
  translateKeywords = true;
  isGlossaryAvailable = false;

  @ViewChildren('component')
  private readonly components!: QueryList<componentGroup>;
  @ViewChildren('control')
  private readonly controls!: QueryList<SingleSelectComponent>;

  constructor(
      private readonly changeRefDetector: ChangeDetectorRef,
      private readonly translationService: TranslationService) {}

  ngOnInit() {
    this.languages = this.translationService.getLanguages();
  }

  ngAfterViewInit() {
    for (const control of this.controls) {
      this.form.addControl(control.controllerName!, control.control);
    }
    this.addLanguageValidators();
    this.form.valueChanges.subscribe(() => {
      this.translationValidationErrorEvent.emit(this.hasFormError());
    });
    this.changeRefDetector.detectChanges();
  }

  glossarySelection(value: SelectionGroup) {
    const glossary = value as Selection;
    // Only set the glossary ID if the glossary object is valid because the
    // glossary selection has no validation.
    if (glossary) {
      this.glossaryId = glossary['id'];
    }
  }

  sourceLanguageSelection(value: SelectionGroup) {
    const language = value as Selection;
    this.sourceLanguageCode = language['code'];
  }

  targetLanguageSelection(value: SelectionGroup) {
    const language = value as Selection;
    this.targetLanguageCode = language['code'];
  }

  disableForm(disable: boolean) {
    // Only include the glossary control when glossaries are available otherwise
    // when this function gets called it'll enable/disable the glossary control
    // regardless if it has data or not.
    if (this.isGlossaryAvailable) {
      this.disableFormControl(TranslationControl.GLOSSARY, disable);
    }
    this.disableFormControl(TranslationControl.SOURCE_LANGUAGE, disable);
    this.disableFormControl(TranslationControl.TARGET_LANGUAGE, disable);
    for (const component of this.components) {
      component.setDisabledState(disable);
    }
  }

  disableFormControl(control: string, disable: boolean) {
    const formControl = this.getFormControls()[control];
    (disable) ? formControl.disable() : formControl.enable();
  }

 getGlossaries() {
    this.showSpinner = true;
    console.log('Glossaries requested.');
    this.translationService.getGlossaries().subscribe(
        (response => {
          this.isGlossaryAvailable = true;
          this.showSpinner = false;
          this.glossaries = response.body!;
          const controls = this.getFormControls();
          const sourceLanguageControl =
              controls[TranslationControl.SOURCE_LANGUAGE];
          const targetLanguageControl =
              controls[TranslationControl.TARGET_LANGUAGE];
          // Glossary control should only be enabled when the source language
          // and target language controls are enabled. Source and language
          // controls are enabled when accounts are successfully loaded.
          if (sourceLanguageControl.enabled && targetLanguageControl.enabled) {
            this.disableFormControl(TranslationControl.GLOSSARY, false);
          }
          console.log('Glossaries request successful.');
        }),
        (error => {
          this.showSpinner = false;
          console.error(error);
        }));
  }

  getTranslationData(): Translation {
    return {
      sourceLanguageCode: this.sourceLanguageCode!,
      targetLanguageCode: this.targetLanguageCode!,
      glossaryId: this.glossaryId!,
      translateKeywords: this.translateKeywords,
      translateAds: this.translateAds,
      shortenTranslationsToCharLimit: this.shortenTranslationsToCharLimit,
    };
  }

  private addLanguageValidators() {
    const controls = this.getFormControls();

    const sourceLanguageControl = controls[TranslationControl.SOURCE_LANGUAGE];
    const targetLanguageControl = controls[TranslationControl.TARGET_LANGUAGE];

    // See https://angular.io/api/forms/AbstractControl#addvalidators
    sourceLanguageControl.addValidators(
        this.isSameLanguageValidator(TranslationControl.SOURCE_LANGUAGE));
    targetLanguageControl.addValidators(
        this.isSameLanguageValidator(TranslationControl.TARGET_LANGUAGE));

    sourceLanguageControl.updateValueAndValidity();
    targetLanguageControl.updateValueAndValidity();
  }

  private getFormControls(): {[key: string]: FormControl;} {
    return this.form.controls;
  }

  private hasFormError(): boolean {
    const controls = this.getFormControls();
    const result = [];
    for (const control of Object.values(controls)) {
      if (control.errors) {
        result.push(control.errors);
      }
    }
    return result.length > 0;
  }

  // TODO(): Consider creating abstract/base class for validators as
  // there are other custom validators in the repository.
  private isSameLanguageValidator(translationControl: string): ValidatorFn {
    return (control: AbstractControl): ValidationErrors|null => {
      const language =
          (translationControl === TranslationControl.SOURCE_LANGUAGE ?
               this.targetLanguageCode :
               this.sourceLanguageCode);
      const value = control.value?.['code'];
      // Only proceed with the validation check if the value of the language
      // field or the value of the language to compare it to is defined.
      // Otherwise the validation will trigger on load which is not desired.
      if (!language || !value) {
        return null;
      }
      const isSameLanguage = (value === language);
      return isSameLanguage ? {sameLanguage: {value}} : null;
    };
  }
}
